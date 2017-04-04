from   pipeline.compilers import CompilerBase
import sass


class SassCompiler(CompilerBase):
    output_extension = 'css'

    def match_file(self, filename):
        return filename.endswith('.scss')

    def compile_file(self, infile, outfile, outdated=False, force=False):
        compiled_str = sass.compile(filename=infile, output_style='expanded')
        with open(outfile, 'w', encoding='utf-8') as compiled_file:
            compiled_file.write(compiled_str)
