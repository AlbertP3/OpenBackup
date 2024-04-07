import os
from subprocess import run
from abc import ABC


class AgnosticBase(ABC):

    SWD = os.path.dirname(os.path.abspath(__file__))

    def parse_config(self, config: dict) -> dict:
        self.SWD = os.path.normpath(self.SWD)
        config["settings"]["logfile"] = os.path.normpath(config["settings"]["logfile"])
        config["settings"]["defaultdst"] = os.path.normpath(
            config["settings"].get("defaultdst", ".")
        )
        for i, v in enumerate(config["settings"].setdefault("mkdirs", [])):
            config["settings"]["mkdirs"][i] = os.path.normpath(v)
        batch_id = 0
        for i, v in enumerate(config["paths"]):
            config["paths"][i]["batch_id"] = batch_id
            config["paths"][i]["src"] = os.path.normpath(v["src"])
            try:
                config["paths"][i]["dst"] = os.path.normpath(v["dst"])
            except KeyError:
                config["paths"][i]["dst"] = config["settings"]["defaultdst"]
            batch_id += 1
        return config


class LinuxBase:

    FN = type("Functions", (object,), {"rm": "rm", "rmrf": "rm -rf", "exe": "sh"})()

    @staticmethod
    def execute(tempfile):
        """Runs the backup script"""
        run(["chmod", "+x", tempfile])
        run([f"./{tempfile}"], shell=True)


class PythonBase:

    FN = type("Functions", (object,), {"exe": "py", "rm": "rm"})()

    @staticmethod
    def execute(tempfile):
        """Runs the backup script"""
        run([f"python3 ./{tempfile}"], shell=True)
