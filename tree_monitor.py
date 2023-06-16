import os
import re
from copy import deepcopy
from time import perf_counter
from base import BasicGenerator


class TreeMonitor(BasicGenerator):
    '''Supports rsync in detecting files that were deleted/renamed/moved. 
       Recursively compares directory tree between destination and source and parses the result to actions.
       **To be used only for incremental backups** - all surplus files from destination will be marked for deletion'''

    def __init__(self, config:dict):
        self.config = deepcopy(config['rsync'])
        self.expand_paths()

    def generate(self) -> list:
        self._files_scanned = 0
        self.out = list()
        self.collect_diff()
        self.filter_diff()
        self.gen_actions()
        return self.out

    def collect_diff(self):
        '''Build a set of files that are present only on the target'''
        t0 = perf_counter()
        self.diff = set()
        for path in self.config['paths']:
            excl = self.parse_rsync_exclude(path.get('exclude'))
            parsed_src = set()
            for sub_path in self.btr(path['src'], excl):
                parsed_src.add(self.get_target_path({**path, 'src': sub_path}))
            tgt_files = self.btr(self.get_start_path(path), excl)
            [self.diff.add(f) for f in tgt_files.difference(parsed_src) 
                if not any(d in f for d in self.config['settings'].get('mkdirs', list()))]
            self._files_scanned+=len(parsed_src)
        print(f'Scanned {self._files_scanned:,} files in {perf_counter()-t0:.2f} seconds')

    def btr(self, rootdir:str, exclude:re.Pattern) -> set:
        '''Build Tree Recursive'''
        self.__btr_res = set()
        self.__btr_exc = exclude
        self.__build_tree_recursive(rootdir)
        return self.__btr_res

    def __build_tree_recursive(self, rootdir:str):
        try:
            for f in os.listdir(rootdir):
                path = f"{rootdir}/{f}"
                if self.__btr_exc.search(path):
                    continue
                self.__btr_res.add(path)
                if os.path.isdir(path):
                    self.__build_tree_recursive(path)
        except FileNotFoundError:
            pass
        except NotADirectoryError:
            self.__btr_res.add(rootdir)

    # TODO implement proper parsing
    def parse_rsync_exclude(self, excl:list) -> re.Pattern:
        '''Parses the rsync glob patterns to regex'''
        if not excl: res = r'.^'
        else:
            res = '(' + '|'.join(p[1:-1] for p in excl) + ')'
        return re.compile(res)

    def gen_actions(self):
        actions = {self.parse_path(p) for p in self.diff}
        self.out.extend([*{f"rm -rfv {f} | tee -a {self.config['settings']['rlogfilename']}" for f in actions}])

    def expand_paths(self):
        '''If path contains {x,y,...} expression then 
           it will be divided into separate 'plain' paths'''
        to_del = set()
        to_add = list()
        for i, v in enumerate(self.config['paths']):
            if '{' in v['src']:
                lbi = v['src'].find('{')
                rbi = v['src'].find('}')
                pre_path = v['src'][:lbi]
                exp_paths = v['src'][lbi+1:rbi].split(',')
                post_path = v['src'][rbi+1:]
                post_path.replace('}', '')
                for e in exp_paths:
                    src = f"{pre_path}{e}{post_path}"
                    to_add.append({**v, 'src': src})
                to_del.add(i)
        self.config['paths'] = [v for i, v in enumerate(self.config['paths']) if i not in to_del]
        for p in to_add:
            self.config['paths'].append(p)
        
    def filter_diff(self):
        '''Remove unwanted elements from the diff'''
        for d in self.diff.copy():
            if os.path.isdir(d):
                # if a dir is removed, dont't include files
                self.diff = {i for i in self.diff if not i.startswith(d)}
                self.diff.add(d)
