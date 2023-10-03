import os
import re
from time import perf_counter
from base import BasicGenerator


class TreeMonitor(BasicGenerator):
    '''Supports rsync in detecting files that were deleted/renamed/moved. 
       Recursively compares directory tree between destination and source and parses the result to actions.
       **To be used only for incremental backups** - all surplus files from destination will be marked for deletion'''

    def __init__(self, config:dict):
        self.config = config
        self.mkdir_paths = {d for d in self.config['rsync']['settings']['mkdirs']}

    def generate(self) -> list:
        self._files_scanned = 0
        self.out = list()
        self.collect_diff()
        self.gen_actions()
        return self.out

    def collect_diff(self):
        '''Build a set of files that are present only on the target'''
        t0 = perf_counter()
        self.diff = set()
        for path in self.get_expanded_paths(self.config['rsync']['paths']):
            if any(k in path.keys() for k in {'archive', 'extract'}):
                continue
            excl = self.parse_rsync_exclude(path.get('exclude'))
            parsed_src = self.__get_parsed_src(path, excl)
            tgt_files = self.btr(self.get_target_path({**path, 'src': os.path.basename(path['src'])}), excl)
            self.diff|=self.filter_diff(tgt_files.difference(parsed_src))
            self._files_scanned+=len(parsed_src)
        self.diff = {f for f in self.diff if not any(p in f for p in self.mkdir_paths)}
        print(f'Scanned {self._files_scanned:,} files in {perf_counter()-t0:.2f} seconds')

    def __get_parsed_src(self, path, excl) -> set:
        parsed_src = set()
        lcompi = path['src'].rfind('/')+1
        for sub_path in self.btr(path['src'], excl):
                parsed_src.add(self.get_target_path({**path, 'src': sub_path[lcompi:]}))
        return parsed_src

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

    def gen_actions(self):
        actions = sorted([self.parse_path(p) for p in self.diff])
        self.out.extend([f"rm -rfv {f} | tee -a {self.config['rsync']['settings']['rlogfilename']}" for f in actions])

    def get_expanded_paths(self, paths:list) -> list:
        '''If path contains {x,y,...}, then it will be divided into separate 'plain' paths'''
        to_del, to_add, exp_paths = set(), list(), list()
        for i, v in enumerate(paths):
            if '{' in v['src']:
                lbi, rbi = v['src'].find('{'), v['src'].find('}')
                pre_path = v['src'][:lbi]
                exp_paths = v['src'][lbi+1:rbi].split(',')
                post_path = v['src'][rbi+1:]
                for e in exp_paths:
                    src = f"{pre_path}{e}{post_path}"
                    to_add.append({**v, 'src': src})
                to_del.add(i)
        exp_paths = [v for i, v in enumerate(paths) if i not in to_del]
        for p in to_add:
            exp_paths.append(p)
        return exp_paths
        
    def filter_diff(self, diff:set) -> set:
        '''Remove unwanted elements from the diff'''
        for d in diff:
            if os.path.isdir(d):
                # if a dir is removed, don't include files
                diff = {i for i in diff if not i.startswith(d)}
                diff.add(d)
        return diff
