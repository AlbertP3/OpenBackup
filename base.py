import os
from subprocess import run
from abc import ABC, abstractmethod


class AgnosticInterface(ABC):

    ext = ""

    @abstractmethod
    def execute(self, temfile: str):
        """Runs the backup script"""
        raise NotImplementedError

    @abstractmethod
    def remove(self, temfile: str):
        """Removes the file"""
        raise NotImplementedError


class LinuxInterface(AgnosticInterface):

    ext = "sh"

    def execute(self, tempfile: str):
        run(["chmod", "+x", tempfile])
        run([f"./{tempfile}"], shell=True)

    def remove(self, tempfile: str):
        run(["rm", tempfile])


class PythonInterface(AgnosticInterface):

    ext = "py"

    def execute(self, tempfile: str):
        run([f"python3 ./{tempfile}"], shell=True)

    def remove(self, tempfile: str):
        os.remove(tempfile)
