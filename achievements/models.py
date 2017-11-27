import collections

from django.db        import models as md
from django.db.models import Q

from users.models import User
from core.models  import Contest
from core.models  import Problem
from core.models  import Attempt

AchievementStatus = collections.namedtuple('AchievementStatus', 'achievement unlocked earned_at progress_percent')

class Achievement(md.Model):
    name        = md.CharField(max_length=255)
    description = md.TextField(null=True, blank=True, default=None)
    points      = md.PositiveIntegerField()
    icon_path   = md.CharField(max_length=255, null=True, blank=True, default=None)
    created_at  = md.DateTimeField(auto_now_add=True)
    updated_at  = md.DateTimeField(auto_now=True)
    # filters:
    amount      = md.IntegerField(null=True, blank=True, default=None)
    problem     = md.ForeignKey(Problem, null=True, blank=True, default=None)
    contest     = md.ForeignKey(Contest, null=True, blank=True, default=None)
    author      = md.CharField(max_length=255, null=True, blank=True, default=None)
    origin      = md.CharField(max_length=255, null=True, blank=True, default=None)
    language    = md.CharField(max_length=255, null=True, blank=True, default=None)

    class Meta:
        db_table      = 'achievements'
        get_latest_by = 'created_at'

    def status(self, user):
        try:
            info = UserAchievement.objects.get(user=user, achievement=self)
        except UserAchievement.DoesNotExist:
            info = None

        if info is not None:
            return AchievementStatus(self, True, info.earned_at, 100)

        query = Q(user=user) & (Q(result='Accepted') | (Q(result='Tested') & Q(score__gt=99.99)))
        if self.problem:
            query = query & Q(problem=self.problem)
        if self.contest:
            query = query & Q(contest=self.contest)
        if self.author:
            query = query & (Q(problem_in_contest__problem__author__contains=self.author) | Q(problem_in_contest__problem__developer__contains=self.author))
        if self.origin:
            query = query & Q(problem__origin=self.origin)
        if self.language:
            query = query & Q(compiler__highlighter=self.language)
        attempts = Attempt.objects.filter(query).order_by('problem_in_contest__problem', 'time').distinct('problem_in_contest__problem')
        attempts_amount = len(attempts)

        if attempts_amount >= self.amount:
            attempts = sorted(attempts, key=lambda x: x.time)
            earned_at = attempts[self.amount - 1].time
            UserAchievement.objects.create(
                user=user,
                achievement=self,
                earned_at=earned_at
            )
            return AchievementStatus(self, True, earned_at, 100)

        return AchievementStatus(self, False, None, 100 * attempts_amount / self.amount)

    def __str__(self):
        return self.name

class UserAchievement(md.Model):
    user        = md.ForeignKey(User, md.CASCADE)
    achievement = md.ForeignKey(Achievement, md.CASCADE)
    earned_at   = md.DateTimeField(blank=True, null=True)
    created_at  = md.DateTimeField(auto_now_add=True)
    updated_at  = md.DateTimeField(auto_now=True)

    class Meta:
        db_table      = 'user_achievements'
        get_latest_by = 'created_at'
