import os
from subprocess import run
from . import SWD


def create_tree(blueprint: dict, root=f"{SWD}/data"):
    """Make files and directories"""
    for e in blueprint:
        if isinstance(e, dict):
            for k, v in e.items():
                run(["mkdir", "-p", os.path.join(root, k)])
                create_tree(v, os.path.join(root, k))
        else:
            for i in {e}:
                run(["touch", os.path.join(root, i)])


def clear_tree():
    run(["rm", "-r", f"{SWD}/data"])
