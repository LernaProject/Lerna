#!/usr/bin/env python3

import locale
import os
import sys

if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lerna.settings')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
