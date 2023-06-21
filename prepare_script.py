import os
from tree_monitor import TreeMonitor
from base import BasicGenerator



class RsyncGenerator(BasicGenerator):
    '''Generate instructions for the bash script. It employs rsync 
       to upload missing/modified files and a TreeMonitor to track renamed/moved/deleted'''

    def __init__(self, config):
        self.config = config
        self.logpath = self.config['rsync']['settings']['rlogfilename']
    
    def generate(self) -> list:
        '''Create a list of all operations - foundament of the bash script'''
        self.out:list = list()
        self.gen_header()
        self.gen_logging()
        self.gen_mkdirs()
        self.gen_cmds('pre')
        self.gen_monitor_actions()
        self.gen_rsync()
        self.gen_cmds('post')
        return self.out
    
    def gen_header(self):
        self.out.extend(["#!/usr/bin/env bash", ''])
        self.out.extend(['# Enable Pathname Expansion', 'shopt -s extglob', ''])

    def gen_logging(self):
        self.out.append('# Setup logging')
        self.out.extend([
            f'echo -n > {self.logpath}',
            f'''log="--log-file={self.logpath} --log-file-format={self.config['rsync']['settings']['rlogfileformat']}"''',
            ''
        ])

    def gen_rsync(self):
        self.out.append("# Sync files")
        for v in self.config['rsync']['paths']:
            if v.get('archive') and not v.get('require_closed'):
                self.out.append(self.get_archive_cmd(v))
                continue
            mode = self.config['rsync']['settings']['rconfmode'] if v.get('isconf') else self.config['rsync']['settings']['rmode']
            exclusions = "--exclude={"+','.join(v['exclude'])+"}" if v.get('exclude') else ''
            c = f"""rsync -{mode} {v['src']} {v['dst']} $log {exclusions}"""
            if v.get('require_closed'):
                self.gen_require_closed(c, v)
            else:
                self.out.append(c)

    def gen_cmds(self, which:str):
        '''Generate which:(pre,post) commands if available'''
        if not self.config['rsync']['settings'].get('cmd', {}).get(which): return
        self.out.extend(['', f'# {which.capitalize()} Commands'])
        for c in self.config['rsync']['settings']['cmd'][which]:
            self.out.append(self.parse_cmd(c))

    def gen_require_closed(self, cmd:str, path):
        if path.get('archive'):
            cmd = f"{self.get_archive_cmd(path)}"
        self.out.extend([
            f"if pgrep {path['require_closed']}; then", 
            f'''  echo "ERROR {path['require_closed']} must be closed in order to backup the configuration" >> {self.logpath}''',
            'else', f"  {cmd}", 'fi'
        ])

    def gen_mkdirs(self):
        self.out.append('# Create directories')
        for d in self.config['rsync']['settings'].get('mkdirs', []):
            self.out.append(f"mkdir -p {d}")
        self.out.append('')
        
    def parse_cmd(self, cmd:str) -> str:
        '''Replace special tags with corresponding variables'''
        cmd = cmd.replace(r'${LOG_PATH}', self.logpath)
        return cmd

    def gen_monitor_actions(self):
        monitor = TreeMonitor(self.config)
        self.out.extend(["# Apply changes (renamed/deleted/moved)", *monitor.generate(), ''])
        
    def get_archive_cmd(self, path) -> str:
        tgt = self.get_target_path({'dst': path['dst'], 'src': path['archive']})
        return f"tar -cjf {tgt}.bz2 {path['src']}"
