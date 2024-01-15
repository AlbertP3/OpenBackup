import os
import re
from time import perf_counter
from abc import ABC, abstractmethod



class AgnosticMonitor(ABC):
    '''Supports the sync tool (rsync, ...) in detecting files that were deleted/renamed/moved. 
    Recursively compares directory tree between destination and source and parses the result to actions.
    **To be used only for incremental backups** - all surplus files from destination will be marked for deletion'''

    re_space = re.compile(r'(?<!\\) ')

    @abstractmethod
    def generate(self) -> list:
        '''Create actions from the Monitor results'''
        ...

    def collect_diff(self, paths:list) -> None:
        '''Build a set of files that are present only on the target'''
        self.diff = set()
        for path in paths:
            if any(k in path.keys() for k in {'archive', 'extract'}):
                continue
            excl = self.parse_rsync_exclude(path.get('exclude'))
            parsed_src = self.get_parsed_src(path, excl)
            tgt_files = self.btr(self.get_target_path({**path, 'src': os.path.basename(path['src'])}), excl)
            self.diff|=self.filter_diff(tgt_files.difference(parsed_src))
            self._files_scanned+=len(parsed_src)
        self.diff = {f for f in self.diff if not any(p in f for p in self.mkdir_paths)}

    def get_parsed_src(self, path, excl) -> set:
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
    
    def filter_diff(self, diff:set) -> set:
        '''Remove unwanted elements from the diff'''
        for d in diff:
            if os.path.isdir(d):
                # if a dir is removed, don't include files
                diff = {i for i in diff if not i.startswith(d)}
                diff.add(d)
        return diff

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

    # TODO implement proper parsing
    def parse_rsync_exclude(self, excl:list) -> re.Pattern:
        '''Parses the rsync glob patterns to regex'''
        if not excl: res = r'.^'
        else:
            res = '(' + '|'.join(p[1:-1] for p in excl) + ')'
        return re.compile(res)

    def parse_path(self, path:str) -> str:
        return os.path.normpath(self.re_space.sub(r'\ ', path))
    
    def get_target_path(self, path:dict) -> str:
        return os.path.join(path['dst'], path['src'])



class LinuxMonitor(AgnosticMonitor):

    def __init__(self, config:dict):
        self.config = config
        self.mkdir_paths = {d for d in self.config['settings']['mkdirs']}

    def generate(self) -> list:
        self._files_scanned = 0
        self.out = list()
        t0 = perf_counter()
        self.collect_diff(self.get_expanded_paths(self.config['paths']))
        print(f'Scanned {self._files_scanned:,} files in {perf_counter()-t0:.2f} seconds')
        self.gen_actions()
        return self.out
    
    def gen_actions(self):
        actions = sorted([self.parse_path(p) for p in self.diff])
        self.out.extend([f"rm -rfv {f} | tee -a {self.config['settings']['rlogfilename']}" for f in actions])



class PythonMonitor(AgnosticMonitor):

    def __init__(self, config:dict):
        self.config = config
        self.mkdir_paths = {d for d in self.config['settings']['mkdirs']}
        self.actions = type('Actions', (object,), {
            'cp':'copy', 'rm':'remove', 'up':'update'
        })()
        self.results_ready = False
        self.sync_prec = self.config['settings'].get('sync_precision', 1)

    def generate(self) -> list[dict[str, str, str]]:
        '''Returns list of dicts [{src, dst, action, batch_id}].
           Marks files for: copy, update, delete.
           Does NOT include os-specific instructions'''
        self.results_ready = False
        self._files_seen = 0
        self._files_scanned = 0
        self.batch_id = 0
        self.results = list()
        t0 = perf_counter()
        for path in self.get_expanded_paths(self.config['paths']):
            if any(k in path.keys() for k in {'archive', 'extract'}):
                continue
            self.results.extend(self.get_sync(path))
            self.batch_id+=1
        self.results = self.filtered_sync(self.results)
        self.results.extend(self.get_diff())
        self.results_ready = True
        print(f'Compared {self._files_seen:,} files in {perf_counter()-t0:.2f} seconds')
        return self.results

    def get_sync(self, path:dict) -> list:
        if path.get('isconf', False):
            return [{'src': path['src'], 'dst':path['dst'], 'action': self.actions.cp, 'batch_id': self.batch_id}]
        out = list()
        lcompi = path['src'].rfind('/')+1
        excl = self.parse_rsync_exclude(path.get('exclude'))
        src_tree = self.btr(path['src'], excl)
        for srcpath in src_tree:
            dstpath = self.get_target_path({**path, 'src': srcpath[lcompi:]})
            try:
                # st_mtime precision may vary. Adding <sync_prec> seconds for practical reasons
                if os.stat(srcpath).st_mtime > os.stat(dstpath).st_mtime + self.sync_prec:
                    if os.path.isfile(srcpath):
                        out.append({'src': srcpath, 'dst': dstpath, 'action': self.actions.up,'batch_id': self.batch_id})
                    else:
                        continue
            except FileNotFoundError:
                out.append({'src': srcpath, 'dst': dstpath, 'action': self.actions.cp, 'batch_id': self.batch_id})
        self._files_seen+=len(src_tree)
        return out

    def get_diff(self) -> list:
        out = list()
        self.collect_diff(self.get_expanded_paths(self.config['paths']))
        for fp in self.diff:
            out.append({'src': None, 'dst': fp, 'action': self.actions.rm, 'batch_id': 0})
        return out

    def filtered_sync(self, generated:list[dict[str, str, str]]):
        for i in generated:
            if os.path.isdir(i['dst']):
                generated = [p for p in generated if not p['dst'].startswith(i['dst']) ]
                generated.append(i)
        return generated
