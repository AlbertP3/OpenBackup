from abc import ABC, abstractmethod
import re
import os



class BasicGenerator(ABC):
    re_space = re.compile(r'(?<!\\) ')

    @abstractmethod
    def generate(self) -> list:
        pass

    def get_target_path(self, path:dict) -> str:
        '''Returns path where the file will be stored on destination'''
        try:
            return path['dst'] + '/' + path['src'][path['src'].rfind('/')+1:]
        except KeyError:
            for v in self.config['paths']:
                if path['src'].startswith(v['src']):
                    return v.get('dst', '.') +'/'+ path['src'][v['src'].rfind('/')+1:]
            else:
                return path['src'][path['src'].rfind('/')+1:]
    
    def get_start_path(self, path:dict) -> str:
        '''Returns relative path on destination where the file/dir should exist'''
        try:
            return path['dst']
        except KeyError:
            return f"./{os.path.basename(path['src'])}"

    def parse_path(self, path:str) -> str:
        '''Escape spaces in paths'''
        path = self.re_space.sub('\ ', path)
        return path
