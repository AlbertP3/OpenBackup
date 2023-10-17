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
    FN = type('Functions', (object,), {'content':{'rf':'rm', 'rmrf':'rm -rf', 'exe':'sh'}})()

    def parse_path(self, path:str) -> str:
        return os.path.normpath(self.re_space.sub('\ ', path))

    def parse_config(self, config:dict) -> dict:
        self.SWD = self.parse_path(self.SWD)
        config['rsync']['settings']['rlogfilename'] = self.parse_path(config['rsync']['settings']['rlogfilename'])
        config['rsync']['settings']['defaultdst'] = self.parse_path(config['rsync']['settings'].get('defaultdst', '.'))
        for i, v in enumerate(config['rsync']['settings'].setdefault('mkdirs', [])):
            config['rsync']['settings']['mkdirs'][i] = self.parse_path(v)
        for i, v in enumerate(config['rsync']['paths']):
            config['rsync']['paths'][i]['src'] = self.parse_path(v['src'])
            try:
                config['rsync']['paths'][i]['dst'] = self.parse_path(v['dst'])
            except KeyError:
                config['rsync']['paths'][i]['dst'] = config['rsync']['settings']['defaultdst']
        return config

    def execute(self):
        '''Runs the backup script'''
        run(['chmod', '+x', self.tempfile])
        run([f'./{self.tempfile}'], shell=True)
