import csv

from django.core import management, exceptions

from users.models import User


def instantiate_users(data):
    for login, password_salt, crypted_password, persistence_token, password in data:
        user = User(
            login=login,
            username=login,
            password_salt=password_salt,
            crypted_password=crypted_password,
            persistence_token=persistence_token,
            rights=0x0,
        )
        user.set_password(password)
        yield user


class Command(management.base.BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('csvfile')

    def handle(self, csvfile, **options):
        try:
            with open(csvfile, encoding='utf-8-sig') as f:
                users = list(instantiate_users(csv.reader(f)))
        except (FileNotFoundError, exceptions.ValidationError) as e:
            raise management.CommandError(str(e))
        else:
            self.stdout.write(str(len(User.objects.bulk_create(users))))
