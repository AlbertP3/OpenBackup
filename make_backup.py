import os
import json
from time import perf_counter
from uuid import uuid4
from subprocess import run
from platform import node, system

from base import *
from script_gen import *

if system() == 'Linux':
    SystemBase = LinuxBase
    ScriptGenerator = LinuxScriptGenerator
else:
    raise Exception('Unsupported OS!')



class OpenBackup(SystemBase):
    '''Interactively handles the backup process'''

    def __init__(self):
        self.tempfile = ''
        self.should_run = False

    def make(self):
        try:
            self.load_config()
        except ValueError:
            print('No profile was selected')
            return
        self.prepare_script()
        self.show_output()
        if self.should_run:
            self.execute()
        else:
            print('Operation has been cancelled')
        if self.tempfile:
            run([self.FN.rm, self.tempfile])

    def load_config(self):
        '''Sources config file(s) from the 'profiles' directory. 
           Includes automation: default.json, single file or platform name'''
        profiles = sorted(os.listdir(f"{self.SWD}/profiles"))
        if 'default.json' in profiles:
            selected = 'default.json'
        elif len(profiles) == 1:
            selected = profiles[0]
        elif f"{node()}.json" in profiles:
            selected = f"{node()}.json"
        else:
            for i, v in enumerate(profiles):
                print(f"{i+1}. {v.split('.')[0]}")
            selected = profiles[int(input("Select profile: "))-1]
        self.config = self.parse_config(json.load(open(f'{self.SWD}/profiles/{selected}', 'r')))
        self.editor:list = self.config['settings'].get('editor', [])
        print(f"Loaded {selected}")
    
    def prepare_script(self):
        '''Generate instructions for the backup script'''
        print('Preparing script...')
        gen = ScriptGenerator(self.config)
        self.instructions =  '\n'.join(gen.generate())
    
    def show_output(self):
        '''Present generated script for confirmation.
           If 'editor' is specified then tempfile will be opened with that command. 
           In this case, the script will be executed only if it was saved/modified.
           Without an editor, instructions are printed to stdout and a manual confirmation is required.
           The tempfile can be edited by hand if neccessary'''
        self.gen_temp_file()
        print("Displaying output...")
        if self.editor:
            mtime = os.path.getmtime(self.tempfile)
            run(self.parse_editor_command(self.editor.copy()))
            if os.path.getmtime(self.tempfile) > mtime:
                self.should_run = True
        else:
            print(self.instructions)
            print('\n')
            self.should_run = input('Confirm execution? [Y/n] ').lower() in {'yes', 'y'}
    
    def gen_temp_file(self):
        '''Creates an uniquely named file with the backup instructions.
           It is deleted after self.generate() ends'''
        self.tempfile = f"{str(uuid4())}.{self.FN.exe}"
        open(self.tempfile, 'w').write(self.instructions)

    def parse_editor_command(self, cmd:list) -> list:
        '''Replace special tags with corresponding values'''
        for i, v in enumerate(cmd):
            cmd[i] = v.replace(r'${FILE}', self.tempfile)
        return cmd

    def execute(self):
        '''Wrapper around the script executor'''
        print(f"Running script...")
        t0 = perf_counter()
        super().execute()
        print(f"Executed in {perf_counter()-t0:.2f} seconds")



if __name__ == '__main__':
    try:
        ob = OpenBackup()
        ob.make()
    except KeyboardInterrupt:
        pass
    finally:
        print('Exitting...')
