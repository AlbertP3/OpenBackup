import pytest
from copy import deepcopy
from unittest import TestCase
import logging

from . import SWD, config
from script_gen import LinuxScriptGenerator
from base import AgnosticBase
from tests.scenarios import EXP_GEN_RSYNC, EXP_PREPARE_SCRIPT_ACTIONS, EXP_GENERATE_PREPARE_SCRIPT

logger = logging.getLogger('script_gen_test')


class LinuxPrepareScriptTests(TestCase, AgnosticBase):
    config = deepcopy(config)
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.rsync_generator = LinuxScriptGenerator(self.parse_config(self.config))
        self.rsync_generator.out = list()

    def tearDown(self):
        super().tearDown()

    def test_parse_paths(self):
        '''Verify that paths are parsed correctly'''
        self.assertEqual(self.rsync_generator.config['settings']['rlogfilename'], r'some/pa\ th/test.log')
        for i, v in enumerate(self.rsync_generator.config['paths']):
            self.assertEqual(v['src'], self.parse_path(v['src']))
            self.assertEqual(v['dst'], self.parse_path(v['dst']))
    
    def test_gen_tool_actions(self):
        '''Verify that rsync is generated properly'''
        self.rsync_generator.gen_tool_actions()
        self.assertEqual(self.rsync_generator.out, EXP_GEN_RSYNC)
    
    def test_gen_archive_cmd(self):
        '''Verify that method returns proper value'''
        res = self.rsync_generator.get_archive_cmd({'dst': './dir/folder/arch.tar', 
                                                    'src': '/x/y/file'})
        self.assertEqual(res, '''tar -cf ./dir/folder/arch.tar /x/y/file && echo "Created tar Archive ./dir/folder/arch.tar From /x/y/file" >> some/pa\ th/test.log''')
        res = self.rsync_generator.get_archive_cmd({'dst': './dir/folder/arch.tar', 
                                                    'src': '/x/y/file',
                                                    'exclude': ["*/__.*"]})
        self.assertEqual(res, '''tar -cf ./dir/folder/arch.tar /x/y/file --exclude={*/__.*} && echo "Created tar Archive ./dir/folder/arch.tar From /x/y/file" >> some/pa\ th/test.log''')
    
    def test_gen_post_cmds(self):
        '''Verify that method returns proper value'''
        self.rsync_generator.gen_cmds('post')
        self.assertEqual(self.rsync_generator.out, ['# Post Commands', "echo 'Hello, world'", ''])

    def test_gen_pre_cmds(self):
        '''Verify that method returns proper value'''
        self.rsync_generator.gen_cmds('pre')
        self.assertEqual(self.rsync_generator.out, [ 
            '# Pre Commands', "echo 'Goodbye' | tee some/pa\\ th/test.log", 
            'man tee', ''])

    def test_gen_monitor_actions(self):
        '''Verify that method returns proper value'''
        self.rsync_generator.gen_monitor_actions()
        self.assertEqual(self.rsync_generator.out, EXP_PREPARE_SCRIPT_ACTIONS)

    def test_gen_mkdirs(self):
        '''Verify that method returns proper value'''
        self.rsync_generator.gen_mkdirs()
        self.assertEqual(self.rsync_generator.out, 
            ['# Create directories', 'mkdir -p tests/data/tgt/adj', '']
        )

    @pytest.mark.compound
    def test_generate(self):
        '''Verify that method returns proper value'''
        res = self.rsync_generator.generate()
        self.assertEqual(res, EXP_GENERATE_PREPARE_SCRIPT)



class LinuxPrepareScriptPythonToolTests(TestCase, AgnosticBase):
    config = deepcopy(config)
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.config['settings']['tool'] = 'python'
        self.python_generator = LinuxScriptGenerator(self.parse_config(self.config))
        self.python_generator.out = list()

    def tearDown(self):
        super().tearDown()

    @pytest.mark.compound
    def test_generate(self):
        '''Verify that method returns proper value'''
        res = '\n'.join(self.python_generator.generate())
        self.assertIn(f"cp -rv {SWD}/data/src/dir1/a.txt tests/data/tgt/dir1/a.txt | tee -a some/pa\ th/test.log", res)
        self.assertEqual(res.count('cp -rv'), 8)
        self.assertEqual(res.count('rm -rfv'), 3)
