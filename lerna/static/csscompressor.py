from pipeline.compressors import CompressorBase
import csscompressor


class CSSCompressor(CompressorBase):
  def compress_css(self, css):
    return csscompressor.compress(css)
