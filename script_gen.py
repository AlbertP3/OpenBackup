import os
import re
from abc import ABC, abstractmethod

from monitors import LinuxMonitor, PythonMonitor



class AgnosticScriptGenerator(ABC):

    re_space = re.compile(r'(?<!\\) ')
    newline = "\n"

    @abstractmethod
    def generate(self) -> list:
        '''Prepare the script'''
        ...
    
    def parse_cmd(self, cmd:str) -> str:
        '''Replace special tags with corresponding variables'''
        cmd = cmd.replace(r'${LOG_PATH}', self.logpath)
        return cmd



class LinuxScriptGenerator(AgnosticScriptGenerator):
    '''Generate instructions for the bash script. It employs the rsync 
       to upload missing/modified files and a LinuxMonitor to track renamed/moved/deleted'''

    def __init__(self, config):
        self.config = config
        self.logpath = self.config['settings']['logfile']
        self.compression_options = {'tar': '', 'bz2': 'j', 'gzip': 'z'}
        self.monitor = LinuxMonitor(self.config)
    
    def generate(self) -> list:
        '''Create a list of all operations - foundament of the bash script'''
        self.out:list = list()
        self.gen_header()
        self.gen_logging()
        self.gen_mkdirs()
        self.gen_cmds('pre')
        self.gen_monitor_actions()
        self.gen_tool_actions()
        self.gen_cmds('post')
        return self.out
    
    def gen_header(self):
        self.out.extend(["#!/usr/bin/env bash", ''])
        self.out.extend(['# Enable Pathname Expansion', 'shopt -s extglob', ''])

    def gen_logging(self):
        self.out.append('# Setup logging')
        self.out.extend([
            f'echo -n > {self.logpath}',
            f'''log="--log-file={self.logpath} --log-file-format={self.config['settings']['logfmt']}"''',
            ''
        ])

    def gen_tool_actions(self):
        self.out.append("# Sync files")
        for path in self.config['paths']:
            if path.get('archive'):
                cmd = self.get_archive_cmd(path)
            elif path.get('extract'):
                cmd = self.get_extract_cmd(path)
            else:
                cmd = self.gen_rsync(path)

            if path.get('require_closed'):
                self.gen_require_closed(cmd, path)
            else:
                self.out.extend(cmd)
        self.out.append('')

    def gen_rsync(self, path:dict) -> list:
        mode = self.config['settings']['rconfmode'] if path.get('isconf') else self.config['settings']['rmode']
        return [
            f"rsync -{mode} {path['src']} {path['dst']} $log{self.fmt_excl(path)}"
        ]
    
    def parse_path(self, path:str) -> str:
        return os.path.normpath(self.re_space.sub(r'\ ', path))
    
    def gen_cmds(self, which:str):
        '''Generate which:(pre,post) commands if available'''
        if not self.config['settings'].get('cmd', dict()).get(which): return
        self.out.extend([f'# {which.capitalize()} Commands'])
        for c in self.config['settings']['cmd'][which]:
            self.out.append(self.parse_cmd(c))
        self.out.append('')

    def gen_require_closed(self, cmd:str, path):
        if path.get('archive'):
            cmd = self.get_archive_cmd(path)
        elif path.get('extract'):
            cmd = self.get_extract_cmd(path)
        self.out.extend([
            f"if pgrep {path['require_closed']}; then", 
            f'''\techo "ERROR {path['require_closed']} must be closed in order to backup the configuration" >> {self.logpath}''',
            'else', *[f"\t{c}" for c in cmd], 'fi'
        ])

    def gen_mkdirs(self):
        '''Generate actions for creating mkdirs paths'''
        make_nodes = [d for d in self.config['settings']['mkdirs'] if not os.path.exists(d)]
        if make_nodes:
            self.out.extend(['# Create directories', *[f"mkdir -p {f}" for f in make_nodes], ''])

    def gen_monitor_actions(self):
        if res := self.monitor.generate():
            self.out.extend(["# Apply changes (renamed/deleted/moved)", *res, ''])

    def get_archive_cmd(self, path) -> list:
        ext = path['dst'].split('.')[-1]
        comp = self.compression_options.get(ext, '')
        return [
            f"tar{self.fmt_excl(path)} -c{comp}vf {path['dst']} -C {path['src']} . &>> {self.logpath}"
        ]

    def get_extract_cmd(self, path) -> list:
        ext = path['src'].split('.')[-1]
        comp = self.compression_options.get(ext, '')
        return [
            f"tar -x{comp}vf {path['src']} -C {path['dst']} . &>> {self.logpath}",
            f"rm -v {os.path.join(path['dst'], os.path.basename(path['src']))} | tee -a {self.logpath}"
        ]

    def fmt_excl(self, path:dict) -> str:
        '''Parse exluded patterns for rsync --exclude'''
        try:
            prefix =  " --exclude="
            if len(path['exclude']) == 1:
                return prefix + path['exclude'][0]
            else:
                return prefix + "{" + ','.join(path['exclude']) + "}"
        except KeyError:
            return ""



class PythonScriptGenerator(AgnosticScriptGenerator):
    '''[WIP] Generate instructions for the .py script. Uses the PythonMonitor
       to upload missing/modified and to track renamed/moved/deleted files and dirs.
       It is a simplified generator, missing the following functionalities: 
            require_closed, gen/ext archive, pre/post commands
    '''

    def __init__(self, config):
        self.config = config
        self.monitor = PythonMonitor(self.config)

    def generate(self) -> list:
        out = list()
        out.extend(self.gen_headers())
        out.extend(self.gen_mkdirs())
        # out.extend(self.gen_pre_cmds())
        out.extend(self.gen_rms())
        out.extend(self.gen_cps())
        # out.extend(self.gen_archs())
        # out.extend(self.gen_post_cmds())
        return out

    def gen_headers(self) -> list:
        return [
            'import logging, shutil, os',
            '',
            '# Setup logging', 
            "try:",
                f"\tos.remove('{self.config['settings']['logfile']}')",
            "except FileNotFoundError:",
                "\tpass",
            "logging.basicConfig(",
                f"\tfilename=os.path.realpath('{self.config['settings']['logfile']}'),",
                "\tfilemode='a',",
                "\tformat='%(asctime)s.%(msecs)05d | %(message)s',",
                "\tdatefmt='%H:%M:%S', ",
                "\tlevel='DEBUG'",
            ")",
            'log = logging.getLogger("OpenBackup")',
            '',
            '# Declare functions',
            "def rm(dst):",
                "\tos.remove(dst)",
                "\tlog.info(f'Removed file {dst}')",
            "def rmdir(dst):",
                "\tshutil.rmtree(dst)",
                "\tlog.info(f'Removed directory {dst}')",
            "def cp(src, dst):",
                "\tshutil.copy2(src, dst)",
                "\tlog.info(f'Copied file to {dst}')",
            "def cpdir(src, dst, ignore=None):",
                "\tshutil.copytree(src, dst, ignore=ignore)",
                "\tlog.info(f'Copied directory to {dst}')",
            ''
        ]

    def gen_mkdirs(self) -> list:
        mkdirs = [
            f"os.mkdir('{p}')\nlog.info(f'Created directory {p}')" 
            for p in self.config['settings']['mkdirs']
            if not os.path.exists(p)
        ]
        return [
            '# Create directories',
            *mkdirs,
            ''
        ] if mkdirs else []
    
    def gen_pre_cmds(self) -> list:
        return [
            '# Pre Commands',
            *self.config['settings']['cmd']['pre'],
            ''
        ] if self.config['settings']['cmd']['pre'] else []
    
    def gen_post_cmds(self) -> list:
        return [
            '# Post Commands',
            *self.config['settings']['cmd']['post'],
            ''
        ] if self.config['settings']['cmd']['post'] else []
    
    def gen_rms(self) -> list:
        out = list()
        res = self.monitor.generate(use_cache=True)
        mxdstlen = max(len(path['dst']) for path in res)
        for path in res:
            if path['action'] not in {'remove'}:
                continue
            elif os.path.isfile(path['dst']):
                out.append(f"rm('{path['dst']}'{' '*(mxdstlen-len(path['dst']))})")
            else:
                out.append(f"rmdir('{path['dst']}'{' '*(mxdstlen-len(path['dst'])-3)})")
        return [
            "# Apply changes (renamed/deleted/moved)",
            *sorted(out),
            ''
        ]

    def gen_cps(self) -> list:
        out = list()
        res = self.monitor.generate(use_cache=True)
        batch_map_exclude = {p['batch_id']: p.get('exclude') for p in self.config['paths']}
        for path in res:
            if path['action'] not in {'copy', 'update'}:
                continue
            elif os.path.isfile(path['src']):
                out.append(
                    f"cp({self.newline}\t'{path['src']}',{self.newline}\t'{path['dst']}'{self.newline})"
                )
            else:
                p1 = f"cpdir({self.newline}\t'{path['src']}',{self.newline}\t'{path['dst']}'"
                excl = batch_map_exclude[path['batch_id']]
                p2 = f''',{self.newline}\tignore=shutil.ignore_patterns('{"', '".join(excl)}',){self.newline})''' if excl else '\n)'
                out.append(p1+p2)
        return [
            "# Sync files",
            *sorted(out),
            ''
        ]

    def gen_archs(self) -> list:
        return [
            '# Gen/Ext Archives',
            '# ...',
            ''
        ]
