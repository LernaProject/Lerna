import shlex
import sys

from .base import BaseCompiler

class FPCCompat(BaseCompiler):
    code_name = 'fpc-delphi-compat'

    source_name = 'main.pas'
    binary_name = 'main'
    options = '-dONLINE_JUDGE -So -XS -Mdelphi -O2'
    error_stream = 'stdout'

    if sys.platform.startswith('win'):
        binary_name += '.exe'

    cmd = ['fpc'] + shlex.split(options) + ['-o', binary_name, source_name]

    @classmethod
    def get_config(cls, **kwargs):
        return super().get_config(strict_sv=True, **kwargs)
