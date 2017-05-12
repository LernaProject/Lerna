import argparse

from django.core import management, exceptions
from django.db   import transaction

from core.models  import Contest, UserInContest
from users.models import User


def check_mask(mask):
    try:
        mask % 0
    except TypeError:
        raise argparse.ArgumentTypeError("must contain exactly one '%' placeholder")
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))
    else:
        return mask


def generate_users(mask, info):
    for index, username in info:
        login = mask % index
        password = User.objects.make_random_password()
        user = User(login=login, username=username, rights=0x0)
        user.set_password(password)
        yield user, password


class Command(management.base.BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('listfile', type=argparse.FileType(encoding='utf-8-sig'), help="""
            Text file containing user names, each on a single line.
        """)
        parser.add_argument('login_mask', type=check_mask, help="""
            User login mask (with, e.g., %%02d).
        """)
        parser.add_argument('--start', type=int, default=0, help="""
            Number for the first user (default: %(default)s).
        """)
        parser.add_argument('-c', '--contest', type=int, action='append', help="""
            Contest ID to register the users for. Can be given multiple times.
        """)

    def handle(self, listfile, login_mask, *, start=0, contest=None, **options):
        contest_ids = contest or [ ]
        usernames = [line[:-1] for line in listfile if len(line) > 1]
        listfile.close()
        pairs = list(generate_users(login_mask, enumerate(usernames, start)))
        contests = Contest.objects.in_bulk(contest_ids)
        if len(contests) != len(contest_ids):
            raise management.CommandError('Contests: only %s found' % (contests, ))

        try:
            with transaction.atomic():
                users = User.objects.bulk_create([user for user, password in pairs])
                uics = [UserInContest(user=u, contest=c) for u in users for c in contests.values()]
                UserInContest.objects.bulk_create(uics)
        except exceptions.ValidationError as e:
            raise management.CommandError(str(e))

        for user, password in pairs:
            print(user.username, user.login, password, sep='\t')
