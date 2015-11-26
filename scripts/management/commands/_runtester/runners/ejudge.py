import shlex
from   subprocess import Popen, PIPE

from .base import Config, BaseRunner, Verdict


class EJudgeConfig(Config):
    """
    A configurer that wraps program invocation in `ejudge-execute` call.
    """

    def __init__(self, exe="ejudge-execute", fallback=None, **attrs):
        super().__init__(fallback, **attrs)
        self.cmd = [exe]
        if self.stdout:
            self.cmd.append("--stdout=" + shlex.quote(self.stdout))
        if self.stderr:
            self.cmd.append("--stderr=" + shlex.quote(self.stderr))
        if self.time_limit:
            self.cmd.append("--time-limit-millis=%d" % self.time_limit)
            self.cmd.append("--real-time-limit=%f" % (self.time_limit / 200)) # 5 times greater.
        if self.memory_limit:
            self.cmd.append("--memory-limit")
            self.cmd.append("--max-vm-size=%dM" % self.memory_limit)
            self.cmd.append("--max-stack-size=%dM" % self.memory_limit)
        if self.strict_sv:
            self.cmd.extend(("--secure-exec", "--security-violation"))

    def get_cmd(self, input_name):
        result = self.cmd
        if input_name:
            result = result[:]
            result.append("--stdin=" + shlex.quote(input_name))
        return result + super().get_cmd(None)


_ejudge_verdict_mapping = {
    "OK": Verdict.OK,
    "TL": Verdict.TL,
    "ML": Verdict.ML,
    "RT": Verdict.RT,
    "SV": Verdict.SV,
}


class EJudgeRunner(BaseRunner):
    """
    A runner that invokes an `ejudge-execute` program and parses its output.
    Should be used with `EJudgeConfig`.
    """

    def run(self, input_name):
        with Popen(self.config.get_cmd(input_name), universal_newlines=True, stderr=PIPE) as proc:
            err = proc.communicate()[1]
        verdict = time_used = memory_used = None
        for line in err.splitlines():
            key, value = line.split(": ", 1)
            if key == "Status":
                verdict = _ejudge_verdict_mapping[value]
            elif key == "CPUTime":
                time_used = int(value)
            elif key == "VMSize":
                memory_used = int(value) >> 10
        return (verdict, time_used, memory_used)
