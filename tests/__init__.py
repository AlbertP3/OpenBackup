import os
import json


def parse_config(config:dict):
    '''Transforms config fields so that it can be used in tests'''
    for i, _ in enumerate(config['rsync']['paths']):
        config['rsync']['paths'][i]['src'] = os.path.join(SWD, 'data/src', config['rsync']['paths'][i]['src'])
    config['rsync']['settings']['defaultdst'] = DDP
    config['rsync']['paths'][2]['dst'] = os.path.join('./tests/data/tgt', config['rsync']['paths'][2]['dst'])
    return config


SWD = os.path.dirname(os.path.abspath(__file__))
DDP = os.path.join(SWD, 'data/tgt')
config = parse_config(json.load(open(f"{SWD}/../profiles/test.json", 'r')))
