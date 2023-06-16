import os
from tree_monitor import TreeMonitor
from base import BasicGenerator



class RsyncGenerator(BasicGenerator):
    '''Generate instructions for the bash script. It employs rsync 
       to upload missing/modified files and a TreeMonitor to track renamed/moved/deleted'''

    def __init__(self, config):
        self.SWD = os.path.dirname(os.path.abspath(__file__))
        self.__config = config
        self.config:dict = self.__config['rsync']
        self.settings:dict = self.config['settings']
        self.parse_paths()
        self.logpath = f"{self.settings['rlogfilename']}"
    
    def parse_paths(self):
        '''Parse all available paths - escape spaces'''
        self.settings['rlogfilename'] = self.parse_path(self.settings['rlogfilename'])
        self.SWD = self.parse_path(self.SWD)
        for i in range(len(self.config['paths'])):
            self.config['paths'][i]['src'] = self.parse_path(self.config['paths'][i]['src'])
            try:
                self.config['paths'][i]['dst'] = self.parse_path(self.config['paths'][i]['dst'])
            except KeyError:
                pass

    def generate(self) -> list:
        '''Create a list of all operations - foundament of the bash script'''
        self.out:list = list()
        self.gen_header()
        self.gen_logging()
        self.gen_mkdirs()
        self.gen_monitor_actions()
        self.gen_rsync()
        self.gen_post_cmds()
        return self.out
    
    def gen_header(self):
        self.out.extend(["#!/usr/bin/env bash", ''])
        self.out.extend(['# Enable Pathname Expansion', 'shopt -s extglob', ''])

    def gen_logging(self):
        self.out.append('# Setup logging')
        self.out.extend([
            f'echo -n > {self.logpath}',
            f'''log="--log-file={self.logpath} --log-file-format={self.settings['rlogfileformat']}"''',
            ''
        ])

    def gen_rsync(self):
        self.out.append("# Sync files")
        for v in self.config['paths']:
            if v.get('archive') and not v.get('require_closed'):
                self.out.append(self.get_archive_cmd(v))
                continue
            src = v['src']
            tgt = v.get('dst', '.')
            mode = self.settings['rconfmode'] if v.get('isconf') else self.settings['rmode']
            exclusions = "--exclude={"+','.join(v['exclude'])+"}" if v.get('exclude') else ''
            c = f"""rsync -{mode} {src} {tgt} $log {exclusions}"""
            if v.get('require_closed'):
                self.gen_require_closed(c, v)
            else:
                self.out.append(c)

    def gen_post_cmds(self):
        if not self.settings.get('cmd', {}).get('post'): return
        self.out.extend(['', '# Post Commands'])
        for c in self.settings['cmd']['post']:
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
        for d in self.config['settings'].get('mkdirs', []):
            self.out.append(f"mkdir -p {d}")
        self.out.append('')
        
    def parse_cmd(self, cmd:str) -> str:
        '''Replace special tags with corresponding variables'''
        cmd = cmd.replace(r'${LOG_PATH}', self.logpath)
        return cmd

    def gen_monitor_actions(self):
        monitor = TreeMonitor(self.__config)
        self.out.extend(["# Apply changes (renamed/deleted/moved)", *monitor.generate(), ''])
        
    def get_archive_cmd(self, path) -> str:
        dst = path['src']
        src = os.path.dirname(self.get_target_path(path))
        return f"tar -cjf {src}/{path['archive']}.bz2 {dst}"
