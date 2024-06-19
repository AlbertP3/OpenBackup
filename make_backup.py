import os
import json
from time import perf_counter
from uuid import uuid4
from subprocess import run
from platform import node, system

from base import *
from script_gen import *


class OpenBackup:
    """Interactively handles the backup process"""

    SWD = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        self.tempfile = ""
        self.should_run = False

    def make(self):
        try:
            self.load_config()
        except ValueError:
            print("No profile was selected")
            return
        self.prepare_script()
        self.show_output()
        if self.should_run:
            self.execute()
        else:
            print("Operation has been cancelled")
        if self.tempfile:
            self.os_int.remove(self.tempfile)

    def load_config(self):
        """Sources config file(s) from the 'profiles' directory.
        Includes automation: default.json, single file or platform name"""
        profiles = sorted(os.listdir(f"{self.SWD}/profiles"))
        if "default.json" in profiles:
            selected = "default.json"
        elif len(profiles) == 1:
            selected = profiles[0]
        elif f"{node()}.json" in profiles:
            selected = f"{node()}.json"
        else:
            for i, v in enumerate(profiles):
                print(f"{i+1}. {v.split('.')[0]}")
            selected = profiles[int(input("Select profile: ")) - 1]
        self.config = self.parse_config(
            json.load(open(f"{self.SWD}/profiles/{selected}", "r"))
        )
        self.load_platform_base()
        self.editor: list = self.config["settings"].get("editor", [])
        print(f"Loaded {selected}")

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

    def load_platform_base(self):
        _os = self.__select_os()
        if _os == "linux":
            self.generator = LinuxScriptGenerator(self.config)
            self.os_int = LinuxInterface()
        elif _os == "python":
            self.generator = PythonScriptGenerator(self.config)
            self.os_int = PythonInterface()
        else:
            raise Exception("Unsupported OS!")

    def __select_os(self) -> str:
        """Auto detect current OS if available else recourse to python"""
        _os = self.config["settings"].get("os", "python").lower()
        available_systems = ("linux", "python")
        if _os == "auto":
            _os = system().lower()
            _os = _os if _os in available_systems else "python"
        return _os

    def prepare_script(self):
        """Generate instructions for the backup script"""
        print("Preparing script...")
        self.instructions = "\n".join(self.generator.generate())

    def show_output(self):
        """
        Present generated script for confirmation.
        If 'editor' is specified then tempfile will be opened with that command.
        In this case, the script will be executed only if it was saved/modified.
        Without editor, Y/n prompt is displayed and file can be edited independently
        """
        self.gen_temp_file()
        print("Displaying output...")
        if self.editor:
            mtime = os.path.getmtime(self.tempfile)
            run(self.parse_editor_command(self.editor.copy()))
            if os.path.getmtime(self.tempfile) > mtime:
                self.should_run = True
        else:
            print(f"You can now edit {self.tempfile} in your favourite editor")
            self.should_run = input("Confirm execution (y/n)? ").lower() in {"yes", "y"}

    def gen_temp_file(self):
        """
        Creates an uniquely named file with the backup instructions.
        It is deleted after the backup is done
        """
        name = self.config["settings"].get("name", "job")
        while f"{name}.{self.os_int.ext}" in os.listdir("."):
            name += f"-{str(uuid4())[:8]}"
        self.tempfile = f"{name}.{self.os_int.ext}"
        open(self.tempfile, "w").write(self.instructions)

    def parse_editor_command(self, cmd: list) -> list:
        """Replace special tags with corresponding values"""
        for i, v in enumerate(cmd):
            cmd[i] = v.replace(r"${FILE}", self.tempfile)
        return cmd

    def execute(self):
        """Wrapper around the script executor"""
        print(f"Running script...")
        t0 = perf_counter()
        self.os_int.execute(self.tempfile)
        print(f"Executed in {perf_counter()-t0:.2f} seconds")


if __name__ == "__main__":
    try:
        ob = OpenBackup()
        ob.make()
    except KeyboardInterrupt:
        pass
    finally:
        print("Exitting...")
