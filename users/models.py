import operator

from django.contrib import auth
from django.db      import models as md

from misc.itertools import indexed_groupby


class UserManager(auth.models.BaseUserManager):
    def create_user(self, login, username, password=None, email=None, rights=0x1):
        u = self.model(
            login=login,
            username=username,
            email=self.normalize_email(email),
            rights=rights,
        )
        u.set_password(password)
        u.full_clean()
        u.save(using=self._db)
        return u

    def create_superuser(self, login, username, password, email=None):
        return self.create_user(login, username, password, email, 0x7)


class User(auth.models.AbstractBaseUser):
    login             = md.CharField(unique=True, max_length=255)
    username          = md.CharField(max_length=255)
    email             = md.EmailField(max_length=255, blank=True, null=True)
    created_at        = md.DateTimeField(auto_now_add=True)
    updated_at        = md.DateTimeField(auto_now=True)
    password_salt     = md.CharField(max_length=255, blank=True)
    crypted_password  = md.CharField(max_length=255, blank=True)
    persistence_token = md.CharField(max_length=255, blank=True)
    rights            = md.IntegerField(default=0x1)

    class Meta:
        db_table      = 'users'
        get_latest_by = 'created_at'

    # Auth.
    USERNAME_FIELD  = 'login'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def get_full_name(self):
        return self.username

    get_short_name = get_full_name

    def has_perm(self, perm, obj=None):
        """
        Does the user have a specific permission?
        """
        # Simplest possible answer: Yes, always.
        return True

    def has_module_perms(self, app_label):
        """
        Does the user have permissions to view the app `app_label`?
        """
        # Simplest possible answer: Yes, always.
        return True

    @property
    def is_staff(self):
        return bool(self.rights & 0x4)

    def __str__(self):
        return '{0.username} ({0.login})'.format(self)


def rank_users(users, field_name, start=1):
    for i, j, k, g in indexed_groupby(users, operator.attrgetter(field_name), start=start):
        if i + 1 == j:
            g[0].rank = str(i)
        else:
            rank = '%d-%d' % (i, j - 1)
            for user in g:
                user.rank = rank