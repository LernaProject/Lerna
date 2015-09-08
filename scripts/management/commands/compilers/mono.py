import shlex

from  .base         import BaseCompiler
from ..runners.base import Config

class MonoCSharp(BaseCompiler):
    code_name = "mono-csharp"

    source_name = "main.cs"
    binary_name = "main.exe"

    cmd = ["gmcs", "-o", "-out:" + shlex.quote(binary_name), "-d:ONLINE_JUDGE", source_name]

    @classmethod
    def get_config(cls, **kwargs):
        return MonoConfig(cls.binary_name, **kwargs)

class MonoConfig(Config):
    def __init__(self, binary_name, mono="mono", fallback=None, **kwargs):
        super().__init__(fallback, **kwargs)
        self.cmd = [mono, binary_name]

    def get_cmd(self, input_name):
        assert input_name is None
        return self.cmd
