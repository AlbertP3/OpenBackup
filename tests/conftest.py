import os
import time
from tests.utils import clear_tree, create_tree
from tests.scenarios import SCENARIO_SRC, SCENARIO_TGT
from . import SWD



def pytest_configure():
    '''Called before whole test session starts'''
    os.mkdir(f"{SWD}/data")
    create_tree(SCENARIO_TGT, f"{SWD}/data/tgt")
    time.sleep(0)
    create_tree(SCENARIO_SRC, f"{SWD}/data/src")


def pytest_sessionfinish(session, exitstatus):
    '''Called after whole test run finished'''
    clear_tree()
