from unittest import TestCase
from utils import *


class UtilsTests(TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_parse_path(self):
        self.assertEqual(
            parse_path("/path/to/some file (example) & test*1"),
            r"/path/to/some\ file\ \(example\)\ \&\ test*1",
        )
        self.assertEqual(
            parse_path("/this/path|has>multiple$special#characters"),
            r"/this/path\|has\>multiple\$special\#characters",
        )
        self.assertEqual(
            parse_path("/my_files/{random}_name[example]&test"),
            r"/my_files/{random}_name\[example\]\&test",
        )
        self.assertEqual(
            parse_path(r"/path/esc>char/x\y"),
            r"/path/esc\>char/x\\y",
        )
        self.assertEqual(
            parse_path("/path/u}matched/w{braces/[square]"),
            r"/path/u\}matched/w\{braces/\[square\]",
        )
        self.assertEqual(
            parse_path("\\}/path/escape d/xyz.txt"),
            r"\}/path/escape\ d/xyz.txt",
        )

    def test_esc_sq(self):
        self.assertEqual(esc_sq("/some/path.abc.txt"), "/some/path.abc.txt")
        self.assertEqual(esc_sq("/some/pat'h.abc.txt"), r"/some/pat'\''h.abc.txt")

    def test_esc_dq(self):
        self.assertEqual(esc_dq("/some/path.abc.txt"), "/some/path.abc.txt")
        self.assertEqual(esc_dq('/some/pat"h.abc.txt'), r"/some/pat\"h.abc.txt")
        self.assertEqual(esc_dq('/some/pat\\"h.abc.txt'), r"/some/pat\"h.abc.txt")
