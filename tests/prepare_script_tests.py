from copy import deepcopy
from unittest import TestCase
import logging

from . import SWD, config
from script_gen import LinuxScriptGenerator, PythonScriptGenerator
from base import AgnosticBase
from tests.scenarios import (
    EXP_GEN_RSYNC,
    EXP_PREPARE_SCRIPT_ACTIONS,
    EXP_GENERATE_PREPARE_SCRIPT,
)

log = logging.getLogger("script_gen_test")


class LinuxPrepareScriptTests(TestCase, AgnosticBase):
    config = deepcopy(config)
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.rsync_generator = LinuxScriptGenerator(self.parse_config(self.config))
        self.rsync_generator.out = list()

    def tearDown(self):
        super().tearDown()

    def test_gen_tool_actions(self):
        """Verify that rsync is generated properly"""
        self.rsync_generator.gen_tool_actions()
        self.assertEqual(self.rsync_generator.out, EXP_GEN_RSYNC)

    def test_gen_archive_cmd(self):
        """Verify that method returns proper value"""
        res = self.rsync_generator.get_archive_cmd(
            {"dst": "./dir/folder/arch.tar", "src": "/x/y/file"}
        )
        self.assertEqual(
            res[0],
            r"tar -cvf './dir/folder/arch.tar' -C '/x/y/file' . &>> 'some/pa th/test.log'",
        )
        res = self.rsync_generator.get_archive_cmd(
            {"dst": "./dir/folder/arch.tar", "src": "/x/y/file", "exclude": ["*/__.*"]}
        )
        self.assertEqual(
            res[0],
            r"""tar --exclude='*/__.*' -cvf './dir/folder/arch.tar' -C '/x/y/file' . &>> 'some/pa th/test.log'""",
        )

    def test_gen_post_cmds(self):
        """Verify that method returns proper value"""
        self.rsync_generator.gen_cmds("post")
        self.assertEqual(
            self.rsync_generator.out,
            [
                "# Post Commands",
                "sed -i '/ building\\| sent\\|total size/d' 'some/pa th/test.log'",
                "",
            ],
        )

    def test_gen_pre_cmds(self):
        """Verify that method returns proper value"""
        self.rsync_generator.gen_cmds("pre")
        self.assertEqual(
            self.rsync_generator.out,
            ["# Pre Commands", "echo 'Goodbye' | tee -a 'some/pa th/test.log'", ""],
        )

    def test_gen_monitor_actions(self):
        """Verify that method returns proper value"""
        self.rsync_generator.gen_monitor_actions()
        self.assertEqual(self.rsync_generator.out, EXP_PREPARE_SCRIPT_ACTIONS)

    def test_gen_mkdirs(self):
        """Verify that method returns proper value"""
        self.rsync_generator.gen_mkdirs()
        self.assertEqual(
            self.rsync_generator.out,
            ["# Create directories", "mkdir -p 'tests/data/tgt/adj'", ""],
        )

    def test_generate(self):
        """Verify that method returns proper value"""
        res = self.rsync_generator.generate()
        self.assertEqual(res, EXP_GENERATE_PREPARE_SCRIPT)


class PythonPrepareScriptTests(TestCase, AgnosticBase):

    config = deepcopy(config)
    config["settings"]["os"] = "python"
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.python_generator = PythonScriptGenerator(self.parse_config(self.config))

    def tearDown(self):
        super().tearDown()

    def test_generate(self):
        res = "\n".join(self.python_generator.generate())
        log.debug(res)

    def test_gen_rms(self):
        """Check if correct objects are marked for removal"""
        self.assertListEqual(
            self.python_generator.gen_rms(),
            [
                "# Apply changes (renamed/deleted/moved)",
                f"rm('{SWD}/data/tgt/dir1/dir 4/r_i.ini')",
                f"rm('{SWD}/data/tgt/dir1/r_ b.txt'     )",
                f"rmdir('{SWD}/data/tgt/dir1/r_dir5'    )",
                "",
            ],
        )

    def test_gen_cps(self):
        """Check if correct objects are marked for copy"""
        n = "\n"
        self.assertListEqual(
            self.python_generator.gen_cps(),
            [
                "# Sync files",
                f"cp({n}\t'{SWD}/data/src/dir1/a.txt',{n}\t'{SWD}/data/tgt/dir1/a.txt'{n})",
                f"cp({n}\t'{SWD}/data/src/dir1/b.txt',{n}\t'{SWD}/data/tgt/dir1/b.txt'{n})",
                f"cp({n}\t'{SWD}/data/src/dir1/dir 4/h.html',{n}\t'{SWD}/data/tgt/dir1/dir 4/h.html'{n})",
                f"cp({n}\t'{SWD}/data/src/dir1/dir 4/i.ini',{n}\t'{SWD}/data/tgt/dir1/dir 4/i.ini'{n})",
                f"cp({n}\t'{SWD}/data/src/dir1/dir2/c.csv',{n}\t'{SWD}/data/tgt/dir1/dir2/c.csv'{n})",
                f"cp({n}\t'{SWD}/data/src/dir1/dir2/d.cpp',{n}\t'{SWD}/data/tgt/dir1/dir2/d.cpp'{n})",
                f"cp({n}\t'{SWD}/data/src/g.xml',{n}\t'{SWD}/data/tgt/g.xml'{n})",
                f"cp({n}\t'{SWD}/data/src/h.go',{n}\t'tests/data/tgt/dir1/conf/h.go'{n})",
                f"cpdir({n}\t'{SWD}/data/src/dir1/dir5',{n}\t'{SWD}/data/tgt/dir1/dir5',{n}\tignore=shutil.ignore_patterns('*/venv*', '*/__.*',){n})",
                "",
            ],
        )
