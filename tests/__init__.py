import os
import json


def parse_config(config:dict):
    '''Transforms config fields so that it can be used in tests'''
    for i, _ in enumerate(config['rsync']['paths']):
        config['rsync']['paths'][i]['src'] = os.path.join(SWD, 'data/src', config['rsync']['paths'][i]['src'])
        try:
            config['rsync']['paths'][i]['dst'] = os.path.join(SWD, config['rsync']['paths'][i]['dst'])
        except KeyError:
            pass
    return config


SWD = os.path.dirname(os.path.abspath(__file__))
config = parse_config(json.load(open(f"{SWD}/../profiles/test.json", 'r')))
