from abc import ABC, abstractmethod
import re
import os



class BasicGenerator(ABC):
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
        for i, v in enumerate(config['rsync']['settings']['mkdirs']):
            config['rsync']['settings']['mkdirs'][i] = self.parse_path(v)
        for i, v in enumerate(config['rsync']['paths']):
            config['rsync']['paths'][i]['src'] = self.parse_path(v['src'])
            try:
                config['rsync']['paths'][i]['dst'] = self.parse_path(v['dst'])
            except KeyError:
                config['rsync']['paths'][i]['dst'] = '.'
        return config
