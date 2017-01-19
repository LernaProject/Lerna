from django.conf                 import settings
from django.core.management.base import BaseCommand, CommandError
from django.db                   import transaction
from django.utils                import timezone

import contextlib
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

from ...models   import TesterStatus
from core.models import Attempt, TestInfo


LOG    = 'compiler.log'
INPUT  = 'stdin.txt'
OUTPUT = 'stdout.txt'
ERRLOG = 'stderr.txt' # Just ignored.
EJLOG  = 'ejudge.log'

EJUDGE_VERDICTS = {
    b'OK': 'OK',
    b'TL': 'Time limit exceeded',
    b'ML': 'Memory limit exceeded',
    b'RT': 'Run-time error',
    b'SV': 'Security violation',
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


def collect_executables(path):
    """
    Searches the given path for executable files. Returns a str -> str dict.
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
    Returns verdict, time used and memory (heap) used.
    """

    verdict = time_used = memory_used = None
    for line in binary_str.splitlines():
        key, _, value = line.partition(b': ')
        if key == b'Status':
            verdict = EJUDGE_VERDICTS[value]
        elif key == b'CPUTime':
            time_used = int(value)
        elif key == b'VMSize':
            memory_used = int(value)

    return verdict, time_used, memory_used


class Tester:
    def __init__(self, workdir, force):
        self.workdir = workdir.expanduser()
        try:
            self.workdir.mkdir(parents=True)
        except FileExistsError:
            if not self.workdir.is_dir():
                raise CommandError("'%s' is not a directory" % self.workdir)
            if not force and next(self.workdir.iterdir(), None) is not None:
                answer = input(
                    'Working directory is not empty. All files inside it will be deleted.\n'
                    'Are you sure you want to proceed? [y/N] '
                )
                if answer.strip().lower() not in ('y', 'yes', 'yessir', 'yeah'):
                    sys.exit('Aborted')

        os.chdir(str(self.workdir))

        self.problems_directory = settings.TESTER.get('PROBLEMS_DIRECTORY')
        checkers_directory      = settings.TESTER.get('CHECKERS_DIRECTORY')
        langs_directory         = settings.TESTER.get('LANGS_DIRECTORY')
        if not self.problems_directory or not checkers_directory or not langs_directory:
            raise CommandError('Invalid TESTER settings')

        self.problems_directory = pathlib.Path(self.problems_directory).expanduser().resolve()
        checkers_directory      = pathlib.Path(checkers_directory).expanduser()
        langs_directory         = pathlib.Path(langs_directory).expanduser()

        if not self.problems_directory.is_dir():
            raise CommandError("Invalid problem directory: '%s'" % self.problems_directory)
        if not checkers_directory.is_dir():
            raise CommandError("Invalid checker directory: '%s'" % checkers_directory)
        if not langs_directory.is_dir():
            raise CommandError("Invalid langs directory: '%s'" % langs_directory)

        self.compilation_scripts = collect_executables(langs_directory)
        self.run_scripts         = collect_executables(langs_directory / 'run')
        self.standard_checkers   = collect_executables(checkers_directory)

    def compile(self, source, compiler_code_name):
        proc = subprocess.run(
            [self.compilation_scripts[compiler_code_name]],
            input=source.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        binary = proc.stdout.splitlines()[0].decode() if proc.returncode == 0 else None
        return binary, proc.stderr.decode(errors='replace')

    def locate_checker(self, checker_cmd, probable_path):
        args = shlex.split(checker_cmd)
        if not args:
            print('Checker is empty')
            raise RecoverableError

        if not os.path.isabs(args[0]):
            args[0] = self.standard_checkers.get(args[0], str(probable_path / args[0]))

        if not os.path.isfile(args[0]):
            print('Checker is not found')
            raise RecoverableError

        return args

    def execute(self, args):
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with open(EJLOG, 'wb') as f:
            f.write(proc.stdout)
        verdict, time_used, memory_used = parse_ejudge_protocol(proc.stdout)
        if verdict is None or time_used is None or memory_used is None:
            print('ejudge-execute protocol is violated')
            raise RecoverableError
        return verdict, max(time_used, 1), max(memory_used >> 10, 125)

    def check(self, args, input_file, output_file, answer_file, cwd):
        # Assume the checker is testlib-compatible.
        # Command line may look like "/usr/bin/java check", so we need to chdir.
        result = subprocess.call(args + [input_file, output_file, answer_file], cwd=cwd)
        return { 0: 'OK', 1: 'Wrong answer', 2: 'Presentation error' }.get(result, 'System error')

    def run_tests(self, attempt, tests_path, args, checker_args):
        problem = attempt.problem
        is_school = attempt.contest.is_school

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
            verdict, time_used, memory_used = self.execute(args)
            max_time   = max(max_time, time_used)
            max_memory = max(max_memory, memory_used)
            if verdict == 'OK':
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
                    result=verdict,
                    used_time=(time_used / 1000),
                    used_memory=memory_used,
                )
                if verdict == 'OK':
                    passed_tests += 1
                elif verdict == 'System error':
                    raise RecoverableError
            elif verdict != 'OK':
                attempt.result = '%s on test %d' % (verdict, test_number)
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
        binary, errors = self.compile(attempt.source, attempt.compiler.code_name)
        if errors:
            with open(LOG, 'wb') as f:
                f.write(errors)
        if not binary:
            print('Compilation error')
            attempt.result = 'Compilation error'
            attempt.error_message = errors
            attempt.save()
            return

        # TODO: Add run_name to Compiler.
        run_script = self.run_scripts[attempt.compiler.run_name if False else "dumb"]
        args = [run_script, binary, INPUT, OUTPUT, ERRLOG, str(time_limit), str(memory_limit)]
        tests_path = self.problems_directory / problem.path
        checker_args = self.locate_checker(problem.checker, tests_path)
        self.run_tests(attempt, tests_path, args, checker_args)

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
                            result=None,
                            compiler__code_name__in=self.compilation_scripts,
                            # compiler__run_name__in=self.run_scripts,
                        ).earliest()
                        attempt.result = 'Queued'
                        attempt.save()
                except Attempt.DoesNotExist:
                    time.sleep(1)
                else:
                    with contextlib.suppress(RecoverableError):
                        try:
                            self.process(attempt)
                        except:
                            print('System error')
                            attempt.result = 'System error'
                            attempt.save()
                            raise
                        finally:
                            print()

        except KeyboardInterrupt:
            print()
        except SigTermException:
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
