from django.core import management, exceptions
from django.db   import transaction

from core.models  import Contest, UserInContest
from users.models import User


def generate_users(mask, indices):
    for index in indices:
        login = mask % index
        password = User.objects.make_random_password()
        user = User(login=login, username=login, rights=0x0)
        user.set_password(password)
        yield user, password


class Command(management.base.BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('name_mask', help='User login/name mask (with, e.g., %%02d).')
        parser.add_argument('count', type=int)
        parser.add_argument('--start', type=int, default=0, help="""
            Number for the first user (default: %(default)s).
        """)
        parser.add_argument('-c', '--contest', type=int, action='append', help="""
            Contest ID to register the users for. Can be given multiple times.
        """)

    def handle(self, name_mask, count, *, start=0, contest=None, **options):
        contest_ids = contest or [ ]
        try:
            name_mask % 0
        except TypeError:
            raise management.CommandError("name_mask must contain exactly one '%' placeholder")
        except ValueError as e:
            raise management.CommandError(str(e))

        pairs = list(generate_users(name_mask, range(start, start + count)))
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
            print(user.login, password)
