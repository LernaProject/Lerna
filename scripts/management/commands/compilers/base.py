from abc        import ABC
from subprocess import Popen, PIPE

from ..runners.base import PlainRunConfig

class CompilationError(Exception):
    pass

class BaseCompiler(ABC):
    """
    Abstract base class for the compiler classes.
    Subclasses must redeclare several fields defined below.
    """

    code_name = None # Used to reference the compiler from the DB.
    source_name = None
    binary_name = None
    cmd = None
    error_stream = "stderr"

    def __init__(self):
        assert self.code_name
        assert self.source_name
        assert self.binary_name
        assert self.cmd
        assert self.error_stream in ("stdout", "stderr")

    def compile(self, source):
        self._save_source(source)

        redirection = { self.error_stream: PIPE }
        with Popen(self.cmd, **redirection) as proc:
            msg = proc.communicate() # (out, err)
            if proc.returncode != 0:
                raise CompilationError(msg[self.error_stream == "stderr"].decode(errors="replace"))

    @classmethod
    def get_config(cls, **kwargs):
        return PlainRunConfig(cls.binary_name, **kwargs)

    @classmethod
    def _save_source(cls, source):
        with open(cls.source_name, "w") as f:
            f.write(source)
