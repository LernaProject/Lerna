import sass
from pipeline.compilers import CompilerBase


class SassCompiler(CompilerBase):
    output_extension = 'css'

    def match_file(self, filename):
        print('Checked: ' + filename)
        return filename.endswith('.scss')

    def compile_file(self, infile, outfile, outdated=False, force=False):
        if not outdated and not force:
            return  # No need to recompiled file
        compiled_str = sass.compile(filename=infile, output_style='expanded')
        with open(outfile, "w") as compiled_file:
            print(compiled_str, file=compiled_file)
