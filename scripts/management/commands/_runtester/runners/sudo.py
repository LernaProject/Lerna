import sys
from  .base import Config

if sys.platform.startswith('win'):
    # Simple stub for Windows.
    SudoConfig = lambda user=None, fallback=None, **attrs: Config(fallback, **attrs)
else:
    class SudoConfig(Config):
        """
        A configurer that wraps program invocation in `sudo` call.
        Only available in Linux; Windows version does nothing.
        """

        def __init__(self, user=None, fallback=None, **attrs):
            super().__init__(fallback, **attrs)
            self.cmd = ['sudo', '-u', user] if user else ['sudo']

        def get_cmd(self, input_name):
            return self.cmd + super().get_cmd(input_name)
