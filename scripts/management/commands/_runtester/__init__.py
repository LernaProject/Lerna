import contextlib
from   django.conf                 import settings
from   django.core.management.base import BaseCommand, CommandError
from   django.db                   import transaction
from   django.utils                import timezone
import functools
import itertools
import os
import pathlib
import shlex
import shutil
import signal
import subprocess
import sys
import time

from .compilers  import *
from .runners    import EJudgeConfig, SudoConfig, EJudgeRunner, DevRunner, Verdict
from ....models  import TesterStatus
from core.models import Attempt, TestInfo


COMPILERS = {
    C.code_name: C() for C in (GCC, FPC, Java, FPCCompat, MonoCSharp, GNUFortran)
}

STDOUT = "stdout.txt"
STDERR = "stderr.txt" # Just ignored.

# TODO: Add the standard checkers to the DB.
STANDARD_CHECKERS = "char token line int32 int64 float5".split()

VERDICT_DESCRIPTIONS = {
    Verdict.TL: "Time limit exceeded",
    Verdict.ML: "Memory limit exceeded",
    Verdict.RT: "Run-time error",
    Verdict.SV: "Security violation",
}


class RecoverableError(Exception):
    """
    An error that does not affect the ability to continue testing other solutions.
    """


class SigTermException(BaseException):
    """
    An exception raised when the tester receives `SIGTERM`.
    Note it is derived from `BaseException`, not from `Exception`.
    """


def raise_sigterm(*args):
    raise SigTermException(*args)


def redirect_stdout_to_self(method):
    """
    A method decorator that redirects standard output stream to self.stdout.
    """

    @functools.wraps(method)
    def handle(self, **options):
        prev_ending = self.stdout.ending
        try:
            if self.stdout.ending.endswith('\n'):
                self.stdout.ending = self.stdout.ending[:-1]
            with contextlib.redirect_stdout(self.stdout):
                return method(self, **options)
        finally:
            self.stdout.ending = prev_ending

    return handle


def file_pattern_iter(pattern, start=1):
    """
    Yields index-annotated file names that match the given pattern.
    """

    for i in itertools.count(start):
        file_name = pattern % i
        if not os.path.isfile(file_name):
            return
        yield i, file_name


class Command(BaseCommand):
    help = "Run a contest tester that processes unchecked attempts from the DB"

    def add_arguments(self, parser):
        parser.add_argument("workdir", type=pathlib.Path, help="""
            Tester working directory
        """)
        parser.add_argument("-f", "--force", action="store_true", help="""
            Do not prompt if the working directory is not empty
        """)

    @redirect_stdout_to_self
    def handle(self, *, workdir, force, **options):
        """
        Command entry point.
        """

        try:
            workdir.mkdir()
        except FileExistsError:
            if not workdir.is_dir():
                raise CommandError("`%s` is not a directory" % workdir)
            if not force:
                # Lazy iteration through the directory's contents.
                for filename in workdir.glob("*"):
                    answer = input(
                        "Working directory is not empty. All files inside it will be deleted.\n"
                        "Are you sure you want to proceed? (y/N) "
                    )
                    if answer.strip().lower() not in ('y', "yes", "yessir", "yeah"):
                        sys.exit("Aborted")
                    break

        os.chdir(str(workdir))

        config = settings.TESTER
        self.problem_directory = os.path.expanduser(config.get("PROBLEM_DIRECTORY", ""))
        self.checker_directory = os.path.expanduser(config.get("CHECKER_DIRECTORY", ""))
        self.ejudge_execute = os.path.expanduser(config.get("EJUDGE_EXECUTE", ""))

        if not os.path.isdir(self.problem_directory):
            raise CommandError("Invalid problem directory: `%s`" % self.problem_directory)
        if not os.path.isdir(self.checker_directory):
            raise CommandError("Invalid checker directory: `%s`" % self.checker_directory)

        print("Started in", workdir)
        status = None
        try:
            # Get notified when someone is trying to kill us.
            signal.signal(signal.SIGTERM, raise_sigterm)

            status = TesterStatus()
            while True:
                status.save()
                try:
                    with transaction.atomic():
                        attempt = Attempt.objects.filter(result=None).earliest()
                        attempt.result = "Queued"
                        attempt.save()
                except Attempt.DoesNotExist:
                    time.sleep(1)
                else:
                    with contextlib.suppress(RecoverableError):
                        try:
                            self.handle_attempt(attempt)
                        except:
                            print("System error")
                            attempt.result = "System error"
                            attempt.save()
                            raise
                    print()

        except KeyboardInterrupt:
            print()
        except SigTermException:
            sys.exit()
        finally:
            print("Terminating")
            if status is not None:
                status.delete()

    def handle_attempt(self, attempt):
        # Clear the working directory.
        for entry in os.listdir():
            if os.path.isfile(entry) or os.path.islink(entry):
                os.remove(entry)
            else:
                shutil.rmtree(entry)

        problem = attempt.problem_in_contest.problem
        is_school = attempt.problem_in_contest.contest.is_school
        start_time = timezone.now()
        print(start_time)
        print(attempt)

        try:
            compiler = COMPILERS[attempt.compiler.code_name]
        except (IndexError, KeyError):
            print("Unknown compiler (%s)" % attempt.compiler)
            raise RecoverableError

        print("Compiling (%s)..." % attempt.compiler)
        attempt.result = "Compiling..."
        attempt.save()
        try:
            compiler.compile(attempt.source)
        except CompilationError as e:
            print("Compilation error")
            attempt.result = "Compilation error"
            attempt.error_message = str(e).replace('\n', "<br />")
            attempt.save()
            return

        checker_params = shlex.split(problem.checker)
        if not checker_params:
            print("Checker is empty")
            raise RecoverableError

        test_path = os.path.join(self.problem_directory, problem.path)

        # Locate the checker.
        if not os.path.isabs(checker_params[0]):
            if checker_params[0] in STANDARD_CHECKERS:
                checker_path = self.checker_directory
            else:
                checker_path = test_path
            checker_params[0] = os.path.join(checker_path, checker_params[0])

        if not os.path.isfile(checker_params[0]):
            print("Checker is not found")
            raise RecoverableError

        # Prepare a runner.
        config = compiler.get_config(
            time_limit=problem.time_limit,
            memory_limit=problem.memory_limit,
            stdout=STDOUT,
            stderr=STDERR,
        )

        if self.ejudge_execute:
            runner = EJudgeRunner(config)
            runner.add_config(EJudgeConfig, self.ejudge_execute)
        else:
            runner = DevRunner(config)

        invoker = settings.TESTER.get("INVOKER")
        if invoker:
            runner.add_config(SudoConfig, invoker)

        max_time     = 1 # ms
        max_memory   = 125 # KB
        passed_tests = 0

        msg = "Testing ({0.time_limit_in_secs}s/{0.memory_limit}MB, {0.checker})...".format(problem)
        print(msg)
        print(test_path, os.sep, sep="")
        for test_number, test_file in file_pattern_iter(os.path.join(test_path, problem.mask_in)):
            print(problem.mask_in % test_number)

            attempt.result = "Testing... %d" % test_number
            attempt.save()

            verdict, time_used, memory_used = runner.run(test_file)

            time_used = max(time_used or 0, 1) # ms
            memory_used = max(memory_used or 0, 125) # KB
            max_time = max(max_time, time_used)
            max_memory = max(max_memory, memory_used)

            if verdict != Verdict.OK:
                if is_school:
                    TestInfo.create(
                        attempt=attempt,
                        test_number=test_number,
                        result=VERDICT_DESCRIPTIONS[verdict],
                        used_time=(time_used / 1000),
                        used_memory=memory_used,
                    )
                    continue
                else:
                    attempt.result = "%s on test %d" % (VERDICT_DESCRIPTIONS[verdict], test_number)
                    attempt.used_time = max_time / 1000
                    attempt.used_memory = max_memory
                    attempt.save()
                    break

            # Run the checker.
            result = subprocess.call(
                checker_params + [
                    test_file,
                    STDOUT,
                    os.path.join(test_path, problem.mask_out % test_number),
                ]
            )

            verdict = "OK"
            if result != 0:
                verdict = { 1: "Wrong answer", 2: "Presentation error" }.get(result, "System error")
                if not is_school:
                    attempt.result = "%s on test %d" % (verdict, test_number)
                    attempt.used_time = max_time / 1000
                    attempt.used_memory = max_memory
                    attempt.save()
                    break

            if is_school:
                TestInfo.create(
                    attempt=attempt,
                    test_number=test_number,
                    result=verdict,
                    used_time=(time_used / 1000),
                    used_memory=memory_used,
                )

        else:
            # All the tests have been run.
            if is_school:
                attempt.result = "Tested"
                attempt.score = passed_tests / test_number * 100
            else:
                attempt.result = "Accepted"
            attempt.used_time = max_time / 1000
            attempt.used_memory = max_memory
            attempt.save()

        if is_school:
            print("Score: %.2f%%" % attempt.score)
        else:
            print(attempt.result)

        print("Completed in %.1f seconds." % ((timezone.now() - start_time).microseconds / 1e6))
