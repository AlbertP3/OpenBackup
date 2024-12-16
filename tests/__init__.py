import os
import json


def parse_config(config: dict):
    """Transforms config fields so that it can be used in tests"""
    for i, _ in enumerate(config["paths"]):
        config["paths"][i]["src"] = os.path.join(
            SWD, "data/src", config["paths"][i]["src"]
        )
    config["settings"]["defaultdst"] = DDP
    config["paths"][3]["dst"] = os.path.join(
        "./tests/data/tgt", config["paths"][3]["dst"]
    )
    return config


SWD = os.path.dirname(os.path.abspath(__file__))
DDP = os.path.join(SWD, "data/tgt")
config = parse_config(json.load(open(f"{SWD}/../profiles/example.json", "r")))
