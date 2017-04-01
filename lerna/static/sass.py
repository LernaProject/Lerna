import sass
from pipeline.compilers import CompilerBase


class SassCompiler(CompilerBase):
    output_extension = 'css'

    def match_file(self, filename):
        return filename.endswith('.scss')

    def compile_file(self, infile, outfile, outdated=False, force=False):
        compiled_str = sass.compile(filename=infile, output_style='expanded')
        with open(outfile, "w") as compiled_file:
            print(compiled_str, file=compiled_file)
