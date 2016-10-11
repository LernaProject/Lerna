import sys
from  .base import BaseCompiler

class GNUFortran(BaseCompiler):
    code_name = 'gfortran'

    source_name = 'main.f90'
    binary_name = 'main'

    if sys.platform.startswith('win'):
        binary_name += '.exe'

    cmd = ['gfortran', '-DONLINE_JUDGE', '-O2', '-o', binary_name, source_name]
