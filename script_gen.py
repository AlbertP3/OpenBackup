import os
import re
from abc import ABC, abstractmethod

from monitors import LinuxMonitor, PythonMonitor



class AgnosticScriptGenerator(ABC):

    re_space = re.compile(r'(?<!\\) ')
    MONITORS = {
        'rsync': LinuxMonitor,
        'python': PythonMonitor,
    }

    @abstractmethod
    def generate(self) -> list:
        '''Prepare the script'''
        ...
    
    def parse_cmd(self, cmd:str) -> str:
        '''Replace special tags with corresponding variables'''
        cmd = cmd.replace(r'${LOG_PATH}', self.logpath)
        return cmd



class LinuxScriptGenerator(AgnosticScriptGenerator):
    '''Generate instructions for the bash script. It employs the tool (rsync, python) 
       to upload missing/modified files and a LinuxMonitor to track renamed/moved/deleted'''

    def __init__(self, config):
        self.config = config
        self.logpath = self.config['settings']['rlogfilename']
        self.compression_options = {'tar': '', 'bz2': 'j', 'gzip': 'z'}
        self.tool_fn = {
            'rsync': self.gen_rsync,
            'python': self.gen_python,
        }[self.config['settings']['tool']]
        self.monitor = self.MONITORS[self.config['settings']['tool']](self.config)
    
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
            f'''log="--log-file={self.logpath} --log-file-format={self.config['settings']['rlogfileformat']}"''',
            ''
        ])

    def gen_tool_actions(self):
        self.out.append("# Sync files")
        for path in self.config['paths']:
            if not path.get('require_closed'):
                if path.get('archive'):
                    self.out.append(self.get_archive_cmd(path))
                elif path.get('extract'):
                    self.out.append(self.get_extract_cmd(path))
            c = self.tool_fn(path)
            if path.get('require_closed'):
                self.gen_require_closed(c, path)
            elif c:
                self.out.append(c)
        self.out.append('')

    def gen_rsync(self, path:dict) -> str:
        mode = self.config['settings']['rconfmode'] if path.get('isconf') else self.config['settings']['rmode']
        exclusions = "--exclude={"+','.join(path['exclude'])+"}" if path.get('exclude') else ''
        return f"""rsync -{mode} {path['src']} {path['dst']} $log {exclusions}"""
    
    def gen_python(self, path:dict) -> str:
        res = self.monitor.results if self.monitor.results_ready else self.monitor.generate()
        log = f"tee -a {self.config['settings']['rlogfilename']}"
        out = [
            f"cp -rv {self.parse_path(p['src'])} {self.parse_path(os.path.relpath(p['dst'], '.'))} | {log}" 
                for p in res 
                if p['action'] in {'copy', 'update'} and
                p['batch_id'] == path['batch_id']
            ]
        return '\n'.join(out) 
        
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
            f'''  echo "ERROR {path['require_closed']} must be closed in order to backup the configuration" >> {self.logpath}''',
            'else', f"  {cmd}", 'fi'
        ])

    def gen_mkdirs(self):
        '''Generate actions for creating mkdirs paths'''
        make_nodes = [d for d in self.config['settings']['mkdirs'] if not os.path.exists(d)]
        if make_nodes:
            self.out.extend(['# Create directories', *[f"mkdir -p {f}" for f in make_nodes], ''])

    def gen_monitor_actions(self):
        if self.config['settings']['tool'] == 'rsync':
            res = self.monitor.generate()
        elif self.config['settings']['tool'] == 'python':
            res = self.monitor.generate(use_cache=True)
            res = [f"rm -rfv {self.parse_path(os.path.relpath(f['dst'], '.'))} | tee -a {self.config['settings']['rlogfilename']}" for f in res if f['action']=='remove']
        if res:
            self.out.extend(["# Apply changes (renamed/deleted/moved)", *res, ''])

    def get_archive_cmd(self, path) -> str:
        ext = path['dst'].split('.')[-1]
        comp = self.compression_options.get(ext, '')
        excl = " --exclude={"+','.join(path['exclude'])+"}" if path.get('exclude') else ''
        return f'''tar -c{comp}f {path['dst']} {path['src']}{excl} && echo "Created {ext} Archive {path['dst']} From {path['src']}" >> {self.logpath}'''

    def get_extract_cmd(self, path) -> str:
        ext = path['src'].split('.')[-1]
        comp = self.compression_options.get(ext, '')
        return f'''tar -x{comp}f {path['src']} -C {path['dst']} --strip-components=1 && echo "Extracted {ext} Archive {path['src']} To {path['dst']}" >> {self.logpath}'''



class PythonScriptGenerator(AgnosticScriptGenerator):
    '''[WIP] Generate instructions for the .py script. Uses the PythonMonitor
       to upload missing/modified and to track renamed/moved/deleted files and dirs.
       It is a simplified generator, missing the following functionalities: 
            require_closed, gen/ext archive, pre/post commands
    '''

    def __init__(self, config):
        self.config = config
        self.monitor = self.MONITORS['python'](self.config)

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
            'import logging, psutil, shutil, os',
            '',
            '# Setup logging', 
            "try:",
                f"\tos.remove('{self.config['settings']['rlogfilename']}')",
            "except FileNotFoundError:",
                "\tpass",
            "logging.basicConfig(",
                f"\tfilename=os.path.realpath('{self.config['settings']['rlogfilename']}'),",
                "\tfilemode='a',",
                "\tformat='%(asctime)s.%(msecs)05d | %(message)s',",
                "\tdatefmt='%H:%M:%S', ",
                "\tlevel='DEBUG'",
            ")",
            'logger = logging.getLogger("OpenBackup")',
            '',
            '# Declare functions',
            "def rm(dst):",
                "\tos.remove(dst)",
                "\tlogger.info(f'Removed file {dst}')",
            "def rmdir(dst):",
                "\tshutil.rmtree(dst)",
                "\tlogger.info(f'Removed directory {dst}')",
            "def cp(src, dst):",
                "\tshutil.copy2(src, dst)",
                "\tlogger.info(f'Copied file to {dst}')",
            "def cpdir(src, dst, ignore=None):",
                "\tshutil.copytree(src, dst, ignore=ignore)",
                "\tlogger.info(f'Copied directory to {dst}')",
            ''
        ]

    def gen_mkdirs(self) -> list:
        return [
            '# Create directories',
            *[f"if not os.path.exists('{p}'):\n\tos.mkdir('{p}')\n\tlogger.info(f'Created directory {p}')" 
              for p in self.config['settings']['mkdirs']],
            ''
        ] if self.config['settings']['mkdirs'] else []
    
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
        mxsrclen = max(len(path['src']) for path in res if path['action'] in {'copy', 'update'})
        mxdstlen = max(len(path['dst']) for path in res if path['action'] in {'copy', 'update'})
        for path in res:
            if path['action'] not in {'copy', 'update'}:
                continue
            elif os.path.isfile(path['src']):
                out.append(
                    f"cp('{path['src']}'{' '*(mxsrclen-len(path['src']))}, '{path['dst']}'{' '*(mxdstlen-len(path['dst']))})"
                )
            else:
                p1 = f"cpdir('{path['src']}'{' '*(mxsrclen-len(path['src'])-3)}, '{path['dst']}'{' '*(mxdstlen-len(path['dst']))}"
                excl = batch_map_exclude[path['batch_id']]
                p2 = f''', ignore=shutil.ignore_patterns('{"', '".join(excl)}'))''' if excl else ')'
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
