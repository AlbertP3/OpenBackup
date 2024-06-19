import re
from collections import deque
from os import PathLike

__bm_deque = deque()
spec_chrs = " ()&|;<>$`?~#[]=%:@!"
esc = "\\"
re_path = re.compile(r"(?<!\\)([" + re.escape(spec_chrs) + r"])")
re_path_backslash = re.compile(r"\\(?![" + re.escape(spec_chrs + "{}\\") + r"])")
re_esc_sq = re.compile(r"'")
re_esc_dq = re.compile(r'(?<!\\)"')


def braces_match(s: str, braces: str = r"{}") -> bool:
    prev = "__"
    lb, rb = braces
    __bm_deque.clear()
    for char in s:
        if char == lb and prev != esc:
            __bm_deque.append(char)
        elif char == rb and prev != esc:
            if not __bm_deque:
                return False
            __bm_deque.pop()
        prev = char
    return len(__bm_deque) == 0


def parse_path(path: str) -> PathLike:
    """
    Escape special characters in paths not wrapped in quotes.
    Allows bracket expansion and wildcards
    """
    if not braces_match(path, r"{}"):
        path = path.replace("{", re.escape("{"))
        path = path.replace("}", re.escape("}"))
    path = re_path.sub(r"\\\1", path)
    path = re_path_backslash.sub(r"\\\\", path)
    return path


def esc_sq(path: PathLike) -> PathLike:
    return re_esc_sq.sub(r"'\''", path)


def esc_dq(path: PathLike) -> PathLike:
    return re_esc_dq.sub(r"\"", path)


def sq(text: str):
    """Surround with single quotes"""
    return f"'{text}'"
