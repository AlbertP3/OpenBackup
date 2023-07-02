import re
import os



class BasicGenerator:
    re_space = re.compile(r'(?<!\\) ')
    SWD = os.path.dirname(os.path.abspath(__file__))

    def get_target_path(self, path:dict) -> str:
        '''Returns path where the file will be stored on destination'''
        return os.path.normpath(os.path.join(path['dst'], path['src']))

    def parse_path(self, path:str) -> str:
        '''Parse single path'''
        path = self.re_space.sub('\ ', path)
        return path

    def parse_config(self, config:dict) -> dict:
        self.SWD = self.parse_path(self.SWD)
        config['rsync']['settings']['rlogfilename'] = self.parse_path(config['rsync']['settings']['rlogfilename'])
        config['rsync']['settings']['defaultdst'] = self.parse_path(config['rsync']['settings'].get('defaultdst', '.'))
        for v in config['rsync']['settings'].setdefault('mkdirs', []):
            v['path'] = os.path.normpath(self.parse_path(v['path']))
            v.setdefault('clear', False)
            v.setdefault('ignore', [])
        for i, v in enumerate(config['rsync']['paths']):
            config['rsync']['paths'][i]['src'] = self.parse_path(v['src'])
            try:
                config['rsync']['paths'][i]['dst'] = self.parse_path(v['dst'])
            except KeyError:
                config['rsync']['paths'][i]['dst'] = config['rsync']['settings']['defaultdst']
        return config

    # TODO implement proper parsing
    def parse_rsync_exclude(self, excl:list) -> re.Pattern:
        '''Parses the rsync glob patterns to regex'''
        if not excl: res = r'.^'
        else:
            res = '(' + '|'.join(p[1:-1] for p in excl) + ')'
        return re.compile(res)

    def join_regex(self, regex:list, prepend:str='') -> re.Pattern:
        '''Creates regex pattern from a list of separate expressions'''
        return re.compile(f'{prepend}(' + '|'.join(regex) + ')')
