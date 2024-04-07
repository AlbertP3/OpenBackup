import pytest
import os
import platform
import time
import logging
from subprocess import run
from copy import deepcopy
from unittest import TestCase
from make_backup import OpenBackup
from tests.utils import clear_tree, create_tree
from tests.scenarios import SCENARIO_TGT, SCENARIO_SRC, EXPECTED_TGT_TREE
from . import SWD, config, DDP

log = logging.getLogger("e2e_tests")


@pytest.mark.skipif(platform.system() != "Linux", reason="Unsupported OS!")
class LinuxE2ETests(TestCase):
    config = deepcopy(config)
    config["settings"]["os"] = "linux"
    config["settings"]["logfile"] = "tests/rsync.log"
    config["paths"].append(
        {
            "src": f"{SWD}/data/tgt/dir1/arch.tar",
            "dst": f"{SWD}/data/ext",
            "extract": True,
        }
    )

    def setUp(self) -> None:
        run(["mkdir", f"{SWD}/data/ext"])
        self.ob = OpenBackup()
        self.ob.config = self.ob.parse_config(self.config)
        self.ob.load_platform_base()
        self.ob.editor = []
        self.ob.prepare_script()
        self.ob.gen_temp_file()

    def tearDown(self) -> None:
        self.reset_tree()
        run([self.ob.FN.rm, self.ob.tempfile])

    def get_file_tree(self, root_: str) -> set:
        actual = set()
        for root, dirs, files in os.walk(root_):
            for f in files:
                actual.add(f"{root}/{f}")
            for d in dirs:
                actual.add(f"{root}/{d}")
        return actual

    def reset_tree(self):
        clear_tree()
        os.mkdir(f"{SWD}/data")
        create_tree(SCENARIO_TGT, f"{SWD}/data/tgt")
        time.sleep(0)
        create_tree(SCENARIO_SRC, f"{SWD}/data/src")

    def test_gen(self):
        """Test if script executes properly"""
        self.ob.execute()
        self.__verify_correct_files_on_destination()
        self.__verify_correct_archive_content()

    def __verify_correct_files_on_destination(self):
        self.assertSetEqual(self.get_file_tree(DDP), EXPECTED_TGT_TREE)

    def __verify_correct_archive_content(self):
        self.assertSetEqual(
            self.get_file_tree(f"{SWD}/data/ext"),
            {
                f"{SWD}/data/ext/z.zip",
                f"{SWD}/data/ext/b.bz2",
                f"{SWD}/data/ext/dir7",
                f"{SWD}/data/ext/dir7/t.tar",
                f"{SWD}/data/ext/dir7/__r.rar",
            },
        )


class PythonE2ETests(TestCase): ...
