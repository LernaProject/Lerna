import csscompressor
from   pipeline.compressors import CompressorBase


class CSSCompressor(CompressorBase):
    def compress_css(self, css):
        return csscompressor.compress(css)
