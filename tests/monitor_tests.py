import pytest
import re
import os
from copy import deepcopy
import logging

from unittest import TestCase
from monitors import LinuxMonitor, PythonMonitor
from base import AgnosticBase
from . import SWD, config, DDP

log = logging.getLogger("monitor_tests")


class LinuxMonitorTests(TestCase, AgnosticBase):
    exp_log_path = r"'some/pa th/test.log'"

    def setUp(self):
        super().setUp()
        self.monitor = LinuxMonitor(self.parse_config(deepcopy(config)))

    def tearDown(self):
        super().tearDown()

    def test_get_target_path_1(self):
        """Check if this method works as expected"""
        self.assertEqual(
            self.monitor.get_target_path({"dst": f"{SWD}/dir1", "src": "a.txt"}),
            f"{SWD}/dir1/a.txt",
        )
        self.assertEqual(
            self.monitor.get_target_path({"src": f"./a.txt", "dst": "."}), "a.txt"
        )
        self.assertEqual(
            self.monitor.get_target_path({"src": f"g.xml", "dst": "."}), "g.xml"
        )
        self.assertEqual(
            self.monitor.get_target_path({"src": f"dir5", "dst": "."}), "dir5"
        )
        self.assertEqual(
            self.monitor.get_target_path({"dst": f"{SWD}/dir1/conf", "src": "h.go"}),
            f"{SWD}/dir1/conf/h.go",
        )

    def test_get_target_path_1(self):
        """Check if this method works as expected"""
        self.assertEqual(
            self.monitor.get_target_path({"dst": f"{SWD}", "src": "dir"}), f"{SWD}/dir"
        )
        self.assertEqual(
            self.monitor.get_target_path({"src": f"dir1", "dst": "."}), f"./dir1"
        )
        self.assertEqual(
            self.monitor.get_target_path({"src": f"c.csv", "dst": "."}), f"./c.csv"
        )

    def test_btr_1(self):
        """Check if Tree is built properly"""
        res = self.monitor.btr(
            os.path.join(SWD, "data/src/dir1/dir2"), re.compile(r".^")
        )
        files = {os.path.basename(f) for f in res}
        self.assertEqual(files, {"e.whl", "f.h", "venv", "c.csv", "d.cpp"})

    def test_btr_2(self):
        """Check if Tree is built properly"""
        res = self.monitor.btr(
            os.path.join(SWD, "data/tgt/dir1/dir2"), re.compile(r".^")
        )
        files = {os.path.basename(f) for f in res}
        self.assertEqual(files, {"f.h", "r_n.exe", "venv", "c.csv", "d.cpp"})

    def test_collect_diff(self):
        """Verify return value of collect_diff"""
        self.monitor._files_scanned = 0
        self.monitor.out = list()
        self.monitor.collect_diff(
            self.monitor.get_expanded_paths(self.monitor.config["paths"])
        )
        self.assertEqual(
            self.monitor.diff,
            {f"{DDP}/dir1/r_ b.txt", f"{DDP}/dir1/dir 4/r_i.ini", f"{DDP}/dir1/r_dir5"},
        )
        self.assertEqual(self.monitor._files_scanned, 11)

    def test_filter_diff(self):
        """Verify that diff is filtered correctly"""
        self.monitor._files_scanned = 0
        self.monitor.out = list()
        self.monitor.collect_diff(
            self.monitor.get_expanded_paths(self.monitor.config["paths"])
        )
        self.assertEqual(
            self.monitor.diff,
            {f"{DDP}/dir1/r_ b.txt", f"{DDP}/dir1/dir 4/r_i.ini", f"{DDP}/dir1/r_dir5"},
        )

    def test_parse_rsync_exlude(self):
        """Verify rsync-exclude parser"""
        excl = ["*/venv*", "*/__.*"]
        self.assertEqual(self.monitor.parse_rsync_exclude(excl).pattern, "(/venv|/__.)")

    def test_gen_actions(self):
        """Verify actions are generated properly and sorted"""
        self.monitor.out = list()
        self.monitor.diff = {"a.txt", "dir/b.csv", "dir/hello world.pdf"}
        self.monitor.gen_actions()
        self.assertEqual(
            self.monitor.out,
            [
                rf"rm -rfv 'a.txt' | tee -a {self.exp_log_path}",
                rf"rm -rfv 'dir/b.csv' | tee -a {self.exp_log_path}",
                rf"rm -rfv 'dir/hello world.pdf' | tee -a {self.exp_log_path}",
            ],
        )

    def test_expand_paths(self):
        """Verify that paths are expanded correctly"""
        paths = {
            v["src"]
            for v in self.monitor.get_expanded_paths(self.monitor.config["paths"])
        }
        self.assertIn(f"{SWD}/data/src/h.go", paths)
        self.assertIn(f"{SWD}/data/src/l s.doc", paths)
        self.assertNotIn(f"{SWD}/data/src/" + "{h,go,l s.doc}", paths)
        self.assertEqual(len(paths), 5)

    def test_expand_paths_2(self):
        """Verify that paths are expanded correctly"""
        paths = [{"src": SWD + "/data/{dir1,dir2}/file"}]
        res = self.monitor.get_expanded_paths(paths)
        self.assertEqual(
            res,
            [
                {"src": "{}/data/dir1/file".format(SWD)},
                {"src": "{}/data/dir2/file".format(SWD)},
            ],
        )

    def test_generate(self):
        """Verify that main method works correctly"""
        res = self.monitor.generate()
        self.assertEqual(
            res,
            [
                rf"rm -rfv '{DDP}/dir1/dir 4/r_i.ini' | tee -a {self.exp_log_path}",
                rf"rm -rfv '{DDP}/dir1/r_ b.txt' | tee -a {self.exp_log_path}",
                f"rm -rfv '{DDP}/dir1/r_dir5' | tee -a {self.exp_log_path}",
            ],
        )


class PythonMonitorTests(TestCase, AgnosticBase):

    def setUp(self):
        super().setUp()
        self.monitor = PythonMonitor(self.parse_config(deepcopy(config)))

    def test_generate(self):
        out = self.monitor.generate()
        self.assertIn(
            {
                "src": f"{SWD}/data/src/dir1/a.txt",
                "dst": f"{DDP}/dir1/a.txt",
                "action": "update",
                "batch_id": 0,
            },
            out,
        )
        self.assertIn(
            {
                "src": f"{SWD}/data/src/dir1/b.txt",
                "dst": f"{DDP}/dir1/b.txt",
                "action": "copy",
                "batch_id": 0,
            },
            out,
        )
        self.assertIn(
            {
                "src": f"{SWD}/data/src/h.go",
                "dst": f"tests/data/tgt/dir1/conf/h.go",
                "action": "update",
                "batch_id": 3,
            },
            out,
        )
        self.assertIn(
            {
                "src": None,
                "dst": f"{DDP}/dir1/r_ b.txt",
                "action": "remove",
                "batch_id": 0,
            },
            out,
        )
