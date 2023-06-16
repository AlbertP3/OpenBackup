from unittest import TestCase
from tree_monitor import TreeMonitor
from . import SWD, config



class MonitorTests(TestCase):
    
    def setUp(self):
        super().setUp()
        self.monitor = TreeMonitor(config)

    def tearDown(self):
        super().tearDown()
        self.monitor = TreeMonitor(config)

    def test_get_target_path(self):
        '''Check if this method works as expected'''
        self.assertEqual(self.monitor.get_target_path({
            'dst':f'{SWD}/dir1', 
            'src':'./dir1/a.txt'}), 
            f'{SWD}/dir1/a.txt')
        self.assertEqual(self.monitor.get_target_path({
            'src':f'{SWD}/dir1/a.txt'}), 'a.txt')
        self.assertEqual(self.monitor.get_target_path({
            'src':f'{SWD}/g.xml'}), 'g.xml')
        self.assertEqual(self.monitor.get_target_path({
            'src':f'{SWD}/dir1/dir5'}), 'dir5')
        self.assertEqual(self.monitor.get_target_path({
            'dst':f'{SWD}/dir1/conf', 
            'src':'./h.go'}), 
            f'{SWD}/dir1/conf/h.go')
    
    def test_get_start_path(self):
        '''Check if this method works as expected'''
        self.assertEqual(self.monitor.get_start_path(
            {'dst': f'{SWD}/dir'}),
            f"{SWD}/dir"
        )
        self.assertEqual(self.monitor.get_start_path(
            {'src': f'{SWD}/dir1'}),
            f"./dir1"
        )
        self.assertEqual(self.monitor.get_start_path(
            {'src': f'{SWD}/dir1/dir2/c.csv'}),
            f"./c.csv"
        )
    
    def test_collect_diff(self):
        '''Verify return value of collect_diff'''
        self.monitor._files_scanned = 0
        self.monitor.out = list()
        self.monitor.collect_diff()
        self.assertEqual(self.monitor.diff, 
            {'./dir1/r_ b.txt', './dir1/dir4/r_i.ini',
            './dir1/r_dir5', './dir1/r_dir5/r_j.jpg', './dir1/r_dir5/r_k.rtf'}
        )
        self.assertEqual(self.monitor._files_scanned, 11)

    def test_filter_diff(self):
        '''Verify that diff is filtered correctly'''
        self.monitor._files_scanned = 0
        self.monitor.out = list()
        self.monitor.collect_diff()
        self.monitor.filter_diff()
        self.assertEqual(self.monitor.diff, 
            {'./dir1/r_ b.txt', './dir1/dir4/r_i.ini',
            './dir1/r_dir5'}
        )

    def test_parse_rsync_exlude(self):
        '''Verify rsync-exclude parser'''
        excl = ["*/venv*", "*/__.*"]
        self.assertEqual(self.monitor.parse_rsync_exclude(excl).pattern, '(/venv|/__.)')

    def test_gen_actions(self):
        '''Verify actions are generated properly'''
        self.monitor.out = list()
        self.monitor.diff = {'a.txt', './dir/b.csv', './dir/hello world.pdf'}
        self.monitor.gen_actions()
        self.assertEqual(set(self.monitor.out), {
            r'rm -rfv a.txt | tee -a test.log',
            r'rm -rfv ./dir/hello\ world.pdf | tee -a test.log',
            r'rm -rfv ./dir/b.csv | tee -a test.log'}
        )
    
    def test_expand_paths(self):
        '''Verify that paths are expanded correctly'''
        paths = {v['src'] for v in self.monitor.config['paths']}
        self.assertIn(f'{SWD}/data/src/h.go', paths)
        self.assertIn(f'{SWD}/data/src/l.doc', paths)
        self.assertNotIn(f'{SWD}/data/src/'+'{h,go,l.doc}', paths)
        self.assertEqual(len(paths), 4)

    def test_generate(self):
        '''Verify that main method works correctly'''
        res = self.monitor.generate()
        self.assertEqual(set(res), {
            'rm -rfv ./dir1/r_dir5 | tee -a test.log',
            'rm -rfv ./dir1/dir4/r_i.ini | tee -a test.log',
            'rm -rfv ./dir1/r_\ b.txt | tee -a test.log'
        })
