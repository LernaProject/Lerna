from django.contrib import auth
from django.db      import models

import itertools
import operator


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
    login             = models.CharField(unique=True, max_length=255)
    username          = models.CharField(max_length=255)
    email             = models.EmailField(max_length=255, blank=True, null=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)
    password_salt     = models.CharField(max_length=255, blank=True)
    crypted_password  = models.CharField(max_length=255, blank=True)
    persistence_token = models.CharField(max_length=255, blank=True)
    rights            = models.IntegerField(default=0x1)

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
    for k, g in itertools.groupby(users, key=operator.attrgetter(field_name)):
        g = list(g)
        if len(g) == 1:
            g[0].rank = str(start)
        else:
            rank = '%d-%d' % (start, start + len(g) - 1)
            for user in g:
                user.rank = rank

        start += len(g)


class Achievement(models.Model):
    # TODO: Add the DB index.
    user               = models.ForeignKey(User, db_index=False)
    achievement_number = models.IntegerField()
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'achievements'
        unique_together = ('user', 'achievement_number')
        get_latest_by   = 'created_at'

    def __str__(self):
        return '{0.user}#{0.achievement_number}'.format(self)
