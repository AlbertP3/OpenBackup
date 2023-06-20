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
        return os.path.normpath(os.path.join(path.get('dst', '.'), path['src']))
    
    def get_start_path(self, path:dict) -> str:
        '''Returns relative path on destination where the file/dir should exist'''
        try:
            return path['dst']
        except KeyError:
            return os.path.basename(path['src'])

    def parse_path(self, path:str) -> str:
        '''Escape spaces in paths'''
        path = self.re_space.sub('\ ', path)
        return path
