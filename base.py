import os
from subprocess import run
from abc import ABC, abstractmethod


class AgnosticInterface(ABC):

    ext = ""

    @abstractmethod
    def execute(self, tmpfile: str):
        """Runs the backup script"""
        raise NotImplementedError

    @abstractmethod
    def remove(self, tmpfile: str):
        """Removes the file"""
        raise NotImplementedError

    @abstractmethod
    def validate(self, tmpfile: str) -> tuple[bool, str]:
        """Validate the file. Returns is_success and stdout"""
        raise NotImplementedError


class LinuxInterface(AgnosticInterface):

    ext = "sh"

    def execute(self, tmpfile: str):
        run(["chmod", "+x", tmpfile])
        run([f"./{tmpfile}"], shell=True)

    def remove(self, tmpfile: str):
        run(["rm", tmpfile])

    def validate(self, tmpfile: str) -> tuple[bool, str]:
        proc = run(["bash", "-n", tmpfile], capture_output=True, text=True)
        return proc.returncode == 0, proc.stderr[:-1]


class PythonInterface(AgnosticInterface):

    ext = "py"

    def execute(self, tmpfile: str):
        run([f"python3 ./{tmpfile}"], shell=True)

    def remove(self, tmpfile: str):
        os.remove(tmpfile)

    def validate(self, tmpfile: str) -> tuple[bool, str]:
        return False, ""  # TODO
