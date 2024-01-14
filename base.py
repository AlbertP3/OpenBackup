import re
import os
from subprocess import run
from abc import ABC, abstractmethod


class AgnosticBase(ABC):

    @abstractmethod
    def parse_config(self) -> dict:
        ...

    @abstractmethod
    def execute(self):
        ...



class LinuxBase(AgnosticBase):
    re_space = re.compile(r'(?<!\\) ')
    SWD = os.path.dirname(os.path.abspath(__file__))
    FN = type('Functions', (object,), {'rm':'rm', 'rmrf':'rm -rf', 'exe':'sh'})()

    def parse_path(self, path:str) -> str:
        return os.path.normpath(self.re_space.sub('\ ', path))

    def parse_config(self, config:dict) -> dict:
        self.SWD = self.parse_path(self.SWD)
        config['settings']['rlogfilename'] = self.parse_path(config['settings']['rlogfilename'])
        config['settings']['defaultdst'] = self.parse_path(config['settings'].get('defaultdst', '.'))
        for i, v in enumerate(config['settings'].setdefault('mkdirs', [])):
            config['settings']['mkdirs'][i] = self.parse_path(v)
        for i, v in enumerate(config['paths']):
            config['paths'][i]['src'] = self.parse_path(v['src'])
            try:
                config['paths'][i]['dst'] = self.parse_path(v['dst'])
            except KeyError:
                config['paths'][i]['dst'] = config['settings']['defaultdst']
        return config

    def execute(self):
        '''Runs the backup script'''
        run(['chmod', '+x', self.tempfile])
        run([f'./{self.tempfile}'], shell=True)
