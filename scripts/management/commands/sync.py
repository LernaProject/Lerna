from django.conf import settings
from django.core import management

import os
import shutil


class Command(management.base.BaseCommand):
    help = (
        'Ensure that all deps from requirements satisfied, DB migrated for latest version, '
        'static files collected and minified for production'
    )

    def add_arguments(self, parser):
        parser.add_argument('-P', '--without-pip',
            action='store_true',
            help='Do not sync with pip requirements')
        parser.add_argument('-M', '--without-migrate',
            action='store_true',
            help='Do not migrate DB scheme')
        parser.add_argument('-S', '--without-static',
            action='store_true',
            help='Do not collect static files')

    def handle(self, *, without_pip=False, without_migrate=False, without_static=False, **options):
        print = self.stdout.write
        if not os.path.isdir(settings.BASE_DIR):
            raise management.base.CommandError('Base dir was not found.')

        print('Sync started...')
        os.chdir(settings.BASE_DIR)

        print('Build directory cleanup started...')
        if os.path.exists('build'):
            shutil.rmtree('build')
        os.mkdir('build')
        print('Build directory cleanup done.')

        if not without_pip:
            import pip

            print('Pip install...')
            if pip.main(['install', '--upgrade', '-r', 'requirements.txt']) != 0:
                raise management.base.CommandError('Pip install failed.')
            print('Pip install done.')

        if not without_static:
            print('Static collecting and minification started...')
            print('Logs are in build/logs/piped_static.log')
            os.mkdir('build/logs')
            with open('build/logs/piped_static.log', 'w') as f:
                management.call_command('collectstatic', interactive=False, stdout=f)
            print('Static collecting and minification done.')

        if not without_migrate:
            print('DB scheme migration started...')
            management.call_command('migrate')
            print('DB scheme migration done.')

        print('Sync finished.')
