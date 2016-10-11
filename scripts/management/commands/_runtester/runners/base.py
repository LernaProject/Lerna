from   abc       import ABC, abstractmethod
from   enum      import Enum
from   functools import partial
import sys


class Config:
    """
    A base class for runner configurers. Saves given attributes and returns them.
    Requests for undeclared attributes are forwarded to a fallback configurer.
    """

    def __init__(self, fallback=None, **attrs):
        self.fallback = fallback
        self.attrs = attrs

    def get_cmd(self, input_name):
        return self.fallback.get_cmd(input_name) if self.fallback is not None else []


def _get(method, self):
    try:
        return self.attrs[method]
    except KeyError:
        return getattr(self.fallback, method) if self.fallback is not None else None

for method in ('stdout', 'stderr', 'time_limit', 'memory_limit', 'strict_sv'):
    setattr(Config, method, property(partial(_get, method)))


class PlainRunConfig(Config):
    """
    A configurer that simply runs the specified program.
    """

    def __init__(self, binary_name, fallback=None, **attrs):
        super().__init__(fallback, **attrs)
        self.cmd = [binary_name if sys.platform.startswith('win') else './' + binary_name]

    def get_cmd(self, input_name):
        assert input_name is None
        return self.cmd


Verdict = Enum('Verdict', 'OK TL ML RT SV')


class BaseRunner(ABC):
    """
    An abstract base class for solution runners.
    """

    def __init__(self, config=None):
        self.config = config

    def add_config(self, cls, *args, **attrs):
        self.config = cls(*args, fallback=self.config, **attrs)

    @abstractmethod
    def run(self, input_name):
        """
        Runs the solution with the specified input.

        Returns a 3-element tuple: a verdict, CPU time amount used (in msecs)
        and memory amount used (in KBs).
        """
