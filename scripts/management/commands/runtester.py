from django.conf                 import settings
from django.core.management.base import BaseCommand, CommandError
from django.db                   import transaction
from django.utils                import timezone

import collections
import contextlib
import enum
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

from core.models    import Attempt, TestInfo
from scripts.models import TesterStatus


Settings = collections.namedtuple("Settings", (
    "problems_directory",
    "compilers_directory",
    "runners_directory",
    "checkers_directory",
))

# These three files are a part of public interface: the participant can safely freopen them.
INPUT  = 'input.txt'
OUTPUT = 'output.txt'
ERRLOG = 'error.txt' # Just ignored.

LOG   = 'compiler.log'
EJLOG = 'ejudge.log'


class Verdict(enum.Enum):
    OK = 'OK'
    TL = 'Time limit exceeded'
    IL = 'Idleness limit exceeded'
    ML = 'Memory limit exceeded'
    RT = 'Run-time error'
    SV = 'Security violation'
    WA = 'Wrong answer'
    PE = 'Presentation error'
    SE = 'System error'

    @classmethod
    def from_ejudge_status(cls, status):
        if status not in { 'OK', 'TL', 'ML', 'RT', 'SV' }:
            raise KeyError(status)
        return cls[status]

    @classmethod
    def from_testlib_returncode(cls, code):
        return { 0: cls.OK, 1: cls.WA, 2: cls.PE }.get(code, cls.SE)


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


def read_settings():
    """
    Validates and returns TESTER settings.
    """

    def do_read():
        for prefix in ('problems', 'compilers', 'runners', 'checkers'):
            path = settings.TESTER.get('%s_DIRECTORY' % prefix.upper())
            if not path:
                raise CommandError('Missing %s directory from TESTER settings' % prefix)
            path = pathlib.Path(path).expanduser()
            if not path.is_dir():
                raise CommandError("Invalid %s directory: '%s'" % (prefix, path))
            yield path.resolve()

    return Settings(*do_read())


def collect_executables(path) -> { str: str }:
    """
    Searches the given path for executable files.
    Raises CommandError if there are more than one file with the same name.
    """

    registry = { }
    for entry in path.iterdir():
        if entry.is_file() and entry.stat().st_mode & 0b001001001:
            if entry.stem not in registry:
                registry[entry.stem] = str(entry.resolve())
            else:
                raise CommandError("Cannot have both '%s' and '%s' in '%s'" % (
                    pathlib.Path(registry[entry.stem]).name, entry.name, path,
                ))

    if not registry:
        raise CommandError("No executables found in '%s'" % path)
    return registry


def clean_dir(path):
    """
    Removes every file and directory at the given path.
    """

    for entry in path.iterdir():
        if entry.is_file() or entry.is_symlink():
            entry.unlink()
        else:
            shutil.rmtree(str(entry))


def file_pattern_iter(pattern, start=1):
    """
    Yields index-annotated file names that match the given pattern.
    """

    for i in itertools.count(start):
        file_name = pattern % i
        if not os.path.isfile(file_name):
            return
        yield i, file_name


def parse_ejudge_protocol(binary_str):
    """
    Extracts run statistics from ejudge-execute output.
    Returns verdict, CPU time used, real time used, and memory (heap) used.
    """

    verdict = None
    attrs = { b'CPUTime': 0, b'RealTime': 0, b'VMSize': 0 }
    for line in binary_str.splitlines():
        key, _, value = line.partition(b': ')
        if key == b'Status':
            try:
                verdict = Verdict.from_ejudge_status(value.decode())
            except UnicodeDecodeError:
                raise RecoverableError('ejudge-execute returned malformed Status:', value)
            except KeyError:
                raise RecoverableError('ejudge-execute returned unknown Status:', value)
        elif key in attrs:
            try:
                attrs[key] = int(value)
            except ValueError:
                raise RecoverableError(
                    'ejudge-execute returned malformed %s:' % key.decode(), value)

    if verdict is None:
        raise RecoverableError('ejudge-execute returned no Status')

    return verdict, attrs[b'CPUTime'], attrs[b'RealTime'], attrs[b'VMSize']


class Tester:
    def __init__(self, workdir, force):
        self.workdir = workdir.expanduser()
        try:
            self.workdir.mkdir(parents=True)
        except FileExistsError:
            if not self.workdir.is_dir():
                raise CommandError("'%s' is not a directory" % self.workdir)
            if not force and next(self.workdir.iterdir(), None) is not None:
                print('Working directory is not empty. All files inside it will be deleted.')
                answer = input('Are you sure you want to proceed? [y/N] ')
                if answer.strip().lower() not in ('y', 'yes', 'yessir', 'yeah'):
                    sys.exit('Aborted')

        os.chdir(str(self.workdir))

        # Only self.settings.problems_directory is used later.
        self.settings = read_settings()

        self.compilation_scripts = collect_executables(self.settings.compilers_directory)
        self.run_scripts         = collect_executables(self.settings.runners_directory)
        self.standard_checkers   = collect_executables(self.settings.checkers_directory)

    def compile(self, source, compiler_codename) -> (bytes, str):
        proc = subprocess.run(
            [self.compilation_scripts[compiler_codename]],
            input=source.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc.stdout if proc.returncode == 0 else None, proc.stderr.decode(errors='replace')

    def locate_checker(self, checker_cmd, probable_path) -> [str]:
        args = shlex.split(checker_cmd)
        if not args:
            raise RecoverableError('Checker is empty')

        if not os.path.isabs(args[0]):
            args[0] = self.standard_checkers.get(args[0], str(probable_path / args[0]))

        if not os.path.isfile(args[0]):
            raise RecoverableError('Checker is not found')

        return args

    def execute(self, args, data):
        proc = subprocess.run(args, input=data, stdout=subprocess.PIPE)
        with open(EJLOG, 'wb') as f:
            f.write(proc.stdout)
        verdict, time_used, real_time_used, memory_used = parse_ejudge_protocol(proc.stdout)
        return verdict, max(time_used, 1), max(real_time_used, 1), max(memory_used >> 10, 125)

    def check(self, args, input_file, output_file, answer_file, cwd):
        # Command line may look like "/usr/bin/java check", so we need to chdir.
        result = subprocess.call(args + [input_file, output_file, answer_file], cwd=cwd)
        return Verdict.from_testlib_returncode(result)

    def run_tests(self, attempt, data):
        problem = attempt.problem
        time_limit = problem.time_limit
        is_school = attempt.contest.is_school

        script = self.run_scripts[attempt.compiler.runner_codename]
        args = [script, INPUT, OUTPUT, ERRLOG, str(time_limit), str(problem.memory_limit)]
        tests_path = self.settings.problems_directory / problem.path
        checker_args = self.locate_checker(problem.checker, tests_path)

        max_time     = 1 # ms
        max_memory   = 125 # KB
        passed_tests = 0

        print('Testing...')
        print(tests_path, '*', sep=os.sep)
        output_file = os.path.join(os.getcwd(), OUTPUT)
        for test_number, test_file in file_pattern_iter(str(tests_path / problem.mask_in)):
            print(problem.mask_in % test_number)

            attempt.result = 'Testing... %d' % test_number
            attempt.save()

            shutil.copyfile(test_file, INPUT)
            verdict, time_used, real_time_used, memory_used = self.execute(args, data)
            max_time   = max(max_time, time_used)
            max_memory = max(max_memory, memory_used)
            if verdict is Verdict.TL and time_used < time_limit and real_time_used >= time_limit:
                # ejudge-execute cannot tell TL and IL apart.
                verdict = Verdict.IL
            elif verdict is Verdict.OK:
                verdict = self.check(checker_args,
                    test_file,
                    output_file,
                    problem.mask_out % test_number if problem.mask_out else os.devnull,
                    str(tests_path),
                )

            if is_school:
                TestInfo.objects.create(
                    attempt=attempt,
                    test_number=test_number,
                    result=verdict.value,
                    used_time=(time_used / 1000),
                    used_memory=memory_used,
                )
                if verdict is Verdict.OK:
                    passed_tests += 1
                elif verdict is Verdict.SE:
                    # The checker has probably already reported the problem, so we silently fail.
                    raise RecoverableError
            elif verdict is not Verdict.OK:
                attempt.result = '%s on test %d' % (verdict.value, test_number)
                attempt.used_time = max_time / 1000
                attempt.used_memory = max_memory
                attempt.save()
                break
        else:
            # All the tests have been run.
            if is_school:
                attempt.result = 'Tested'
                attempt.score = passed_tests / test_number * 100
            else:
                attempt.result = 'Accepted'
            attempt.used_time = max_time / 1000
            attempt.used_memory = max_memory
            attempt.save()

        max_time /= 1000
        max_memory /= 1024
        if is_school:
            print('Score: %.2f%% (%.3f sec / %.1f MB)' % (attempt.score, max_time, max_memory))
        else:
            print('%s (%.3f sec / %.1f MB)' % (attempt.result, max_time, max_memory))

    def process(self, attempt):
        problem = attempt.problem
        time_limit = problem.time_limit
        memory_limit = problem.memory_limit
        start_time = timezone.now()
        print(start_time)
        print(attempt)
        print("%s / %s sec / %d MB / %s" % (
            attempt.compiler, problem.time_limit_in_secs, memory_limit, problem.checker,
        ))

        clean_dir(pathlib.Path())

        print('Compiling...')
        attempt.result = 'Compiling...'
        attempt.save()
        data, errors = self.compile(attempt.source, attempt.compiler.codename)
        if errors:
            with open(LOG, 'wb') as f:
                f.write(errors)
        if data is None:
            print('Compilation error')
            attempt.result = 'Compilation error'
            attempt.error_message = errors
            attempt.save()
            return

        self.run_tests(attempt, data)

        print('Completed in %.1f seconds.' % ((timezone.now() - start_time).microseconds / 1e6))

    def run_processing_loop(self):
        print('Started in', self.workdir)
        print()
        status = None
        try:
            # Get notified when someone is trying to kill us.
            signal.signal(signal.SIGTERM, raise_sigterm)

            status = TesterStatus()
            while True:
                status.save()
                try:
                    with transaction.atomic():
                        attempt = Attempt.objects.filter(
                            # TODO: SET NOT NULL.
                            result=None,
                            compiler__codename__in=self.compilation_scripts,
                            compiler__runner_codename__in=self.run_scripts,
                        ).earliest()
                        attempt.result = 'Queued'
                        attempt.save()
                except Attempt.DoesNotExist:
                    time.sleep(1)
                else:
                    try:
                        try:
                            self.process(attempt)
                        except:
                            print('System error')
                            attempt.result = 'System error'
                            attempt.save()
                            raise
                    except RecoverableError as e:
                        if e.args:
                            print(*e.args)
                    finally:
                        print()

        except (KeyboardInterrupt, SigTermException):
            sys.exit()
        finally:
            print('Terminating')
            if status is not None:
                status.delete()


class Command(BaseCommand):
    help = 'Run a contest tester that processes unchecked attempts from the DB'

    def add_arguments(self, parser):
        parser.add_argument('workdir', type=pathlib.Path, help="""
            Tester working directory
        """)
        parser.add_argument('-f', '--force', action='store_true', help="""
            Do not prompt if the working directory is not empty
        """)

    @redirect_stdout_to_self
    def handle(self, *, workdir, force, **options):
        """
        Command entry point.
        """

        Tester(workdir, force).run_processing_loop()
