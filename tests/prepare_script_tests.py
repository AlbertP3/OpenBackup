import pytest
from copy import deepcopy
from unittest import TestCase

from . import SWD, config
from prepare_script import RsyncGenerator
from base import BasicGenerator
from tests.scenarios import EXP_GEN_RSYNC, EXP_PREPARE_SCRIPT_ACTIONS, EXP_GENERATE_PREPARE_SCRIPT



class PrepareScriptTests(TestCase, BasicGenerator):
    config = deepcopy(config)
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.rsync_generator = RsyncGenerator(self.parse_config(self.config))

    def tearDown(self):
        super().tearDown()

    def test_parse_paths(self):
        '''Verify that paths are parsed correctly'''
        self.assertEqual(self.rsync_generator.config['rsync']['settings']['rlogfilename'], 'some/pa\ th/test.log')
        for i, v in enumerate(self.rsync_generator.config['rsync']['paths']):
            self.assertEqual(v['src'], self.parse_path(v['src']))
            self.assertEqual(v['dst'], self.parse_path(v['dst']))
    
    def test_gen_rsync(self):
        '''Verify that rsync is generated properly'''
        self.rsync_generator.out = list()
        self.rsync_generator.gen_rsync()
        self.assertEqual(self.rsync_generator.out, EXP_GEN_RSYNC)
    
    def test_gen_archive_cmd(self):
        '''Verify that method returns proper value'''
        res = self.rsync_generator.get_archive_cmd({'dst': './dir/folder', 
                                                    'src': '/x/y/file', 'archive': 'arc'})
        self.assertEqual(res, 'tar -cjf dir/folder/arc.bz2 /x/y/file')
    
    def test_gen_post_cmds(self):
        '''Verify that method returns proper value'''
        self.rsync_generator.out = list()
        self.rsync_generator.gen_cmds('post')
        self.assertEqual(self.rsync_generator.out, ['# Post Commands', "echo 'Hello, world'"])

    def test_gen_pre_cmds(self):
        '''Verify that method returns proper value'''
        self.rsync_generator.out = list()
        self.rsync_generator.gen_cmds('pre')
        self.assertEqual(self.rsync_generator.out, [ 
            '# Pre Commands', "echo 'Goodbye' | tee some/pa\\ th/test.log", 
            'man tee'])

    def test_gen_monitor_actions(self):
        '''Verify that method returns proper value'''
        self.rsync_generator.out = list()
        self.rsync_generator.gen_monitor_actions()
        self.assertEqual(self.rsync_generator.out[0], EXP_PREPARE_SCRIPT_ACTIONS[0])
        self.assertEqual(set(self.rsync_generator.out[1:]), set(EXP_PREPARE_SCRIPT_ACTIONS[1:]))

    @pytest.mark.compound
    def test_generate(self):
        '''Verify that method returns proper value'''
        res = self.rsync_generator.generate()
        self.assertEqual(set(res), set(EXP_GENERATE_PREPARE_SCRIPT))
