from django.db    import models as md

from users.models import User
from core.models  import Contest
from core.models  import Problem

class Achievement(md.Model):
    name                     = md.CharField(max_length=255)
    description              = md.TextField(blank=True)
    points                   = md.PositiveIntegerField()
    icon_path                = md.CharField(max_length=255)
    created_at               = md.DateTimeField(auto_now_add=True)
    updated_at               = md.DateTimeField(auto_now=True)
    #filters:
    amount                   = md.IntegerField(null=True, blank=True, default=None)
    problem                  = md.ForeignKey(Problem, null=True, blank=True, default=None)
    contest                  = md.ForeignKey(Contest, null=True, blank=True, default=None)
    author                   = md.CharField(max_length=255, null=True, blank=True, default=None)
    origin                   = md.CharField(max_length=255, null=True, blank=True, default=None)

    class Meta:
        db_table      = 'achievements'
        get_latest_by = 'created_at'

class UserAchievement(md.Model):
    user        = md.ForeignKey(User, md.CASCADE)
    achievement = md.ForeignKey(Achievement, md.CASCADE)
    earned_at   = md.DateTimeField(blank=True, null=True)
    created_at  = md.DateTimeField(auto_now_add=True)
    updated_at  = md.DateTimeField(auto_now=True)

    class Meta:
        db_table      = 'user_achievements'
        get_latest_by = 'created_at'
