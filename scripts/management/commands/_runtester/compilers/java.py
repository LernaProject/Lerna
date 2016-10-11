import sys

from  .base         import BaseCompiler
from ..runners.base import Config


class Java(BaseCompiler):
    code_name = 'java'

    binary_name = 'Main'
    source_name = binary_name + '.java'

    cmd = ['javac', '-cp', ''.;*'', source_name]

    @classmethod
    def get_config(cls, **kwargs):
        return JavaConfig(cls.binary_name, **kwargs)


class JavaConfig(Config):
    memory_limit = None

    def __init__(self, binary_name, java='java', fallback=None, **kwargs):
        super().__init__(fallback, **kwargs)
        self.cmd = [java, '-Xmx%dM' % super().memory_limit, '-DONLINE_JUDGE=true', binary_name]
        if not super().memory_limit:
            self.cmd.pop(1)

    def get_cmd(self, input_name):
        assert input_name is None
        return self.cmd
