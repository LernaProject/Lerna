import shlex
import sys

from .base import BaseCompiler

class GCC(BaseCompiler):
    code_name = "g++"

    source_name = "main.cpp"
    binary_name = "main"
    options = "-DONLINE_JUDGE -fno-asm -fno-optimize-sibling-calls -ffloat-store -lm -s -static -O2"

    if sys.platform.startswith("win"):
        binary_name += ".exe"

    cmd = ["g++"] + shlex.split(options) + ["-o", binary_name, source_name]

    @classmethod
    def get_config(cls, **kwargs):
        return super().get_config(strict_sv=True, **kwargs)
