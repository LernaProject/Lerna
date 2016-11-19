from django.core.management.base import BaseCommand
from django.conf import settings
import os
import pip


class Command(BaseCommand):
    help = 'Ensure that all deps from requirements satisfied, DB migrated for latest version, static files collected' \
           ' and minified for production'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--without-pip', action='store_true', help='Do not sync with pip requirements')
        parser.add_argument('-m', '--without-migrate', action='store_true', help='Do not migrate DB scheme')
        parser.add_argument('-s', '--without-static', action='store_true', help='Do not collect static files')

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        exec_path = os.sys.executable
        if not base_dir or not exec_path:
            print('Sync failed: base or python dir was not found')
            return

        os.chdir(base_dir)
        print('Sync started...')

        print('Build directory cleanup started...')
        result = os.system("rm -rf build/*")
        if result:
            print('Build directory cleanup failed, aborting...')
            exit(1)
        print('Build directory cleanup done.')

        if not options['without_pip']:
            print('Pip install...')
            pip.main(["install", "--upgrade", "-r", "requirements.txt"])
            print('Pip install done.')

        if not options['without_static']:
            print('Static collecting and minification started...')
            print('Logs are in build/logs/piped_static.log')
            os.system("mkdir -p build/logs")
            result = os.system(os.sys.executable +
                               " manage.py collectstatic --noinput --clear > build/logs/piped_static.log")
            if result:
                print('Ended with error! Aborting...')
                exit(1)
            print('Static collecting and minification done.')

        if not options['without_migrate']:
            print('DB scheme migration started...')
            result = os.system(os.sys.executable + " manage.py migrate")
            if result:
                print('Ended with error! Aborting...')
                exit(1)
            print('DB scheme migration done.')

        print('Sync finished.')
