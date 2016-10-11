from   contextlib import ExitStack
from   signal     import SIGTERM
from   subprocess import Popen, TimeoutExpired
import time

from .base import BaseRunner, Verdict

class DevRunner(BaseRunner):
    """
    Simple and imperfect solution runner.
    Cannot detect neither ML nor SV. Returns `None` instead of `memory_used`.

    Must be used in development environment only.
    """

    def run(self, input_name):
        timeout = self.config.time_limit or 1000
        output_name = self.config.stdout
        error_name = self.config.stderr
        cmd = self.config.get_cmd(None)

        with ExitStack() as stack:
            stdin = stack.enter_context(open(input_name, 'rb')) if input_name else None
            stdout = stack.enter_context(open(output_name, 'wb')) if output_name else None
            stderr = stack.enter_context(open(error_name, 'wb')) if error_name else None

            start_time = time.clock()
            with Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr) as proc:
                try:
                    try:
                        proc.wait(timeout / 1000)
                        time_used = time.clock() - start_time
                    except:
                        proc.send_signal(SIGTERM)
                        proc.wait() # Until the process dies.
                        raise
                except TimeoutExpired:
                    return (Verdict.TL, timeout, None)

            return (Verdict.OK if proc.returncode == 0 else Verdict.RT, time_used, None)
