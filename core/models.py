from django.core  import validators as val
from django.db    import models as md
from django.urls  import reverse
from django.utils import timezone

from misc         import pandoc
from users.models import User


class Problem(md.Model):
    name      = md.CharField(max_length=80)
    path      = md.CharField(max_length=255)
    author    = md.CharField(max_length=64, blank=True, db_index=True)
    developer = md.CharField(max_length=64, blank=True, db_index=True)
    origin    = md.CharField(max_length=128, blank=True, db_index=True)

    statements_format         = md.CharField(max_length=255,
        default='latex,latex,latex,textile,latex,latex,latex',
        validators=[val.RegexValidator(r'^([^\s,]+,){6}[^\s,]+$')])
    description               = md.TextField()
    input_specification       = md.TextField(blank=True)
    output_specification      = md.TextField(blank=True)
    samples                   = md.TextField(blank=True)
    explanations              = md.TextField(blank=True)
    notes                     = md.TextField(blank=True)
    analysis                  = md.TextField(blank=True)
    description_html          = md.TextField(editable=False)
    input_specification_html  = md.TextField(blank=True, editable=False)
    output_specification_html = md.TextField(blank=True, editable=False)
    samples_html              = md.TextField(blank=True, editable=False)
    explanations_html         = md.TextField(blank=True, editable=False)
    notes_html                = md.TextField(blank=True, editable=False)
    analysis_html             = md.TextField(blank=True, editable=False)

    input_file   = md.CharField(max_length=16, blank=True)
    output_file  = md.CharField(max_length=16, blank=True)
    time_limit   = md.PositiveIntegerField()
    memory_limit = md.PositiveIntegerField()
    checker      = md.CharField(max_length=100)
    mask_in      = md.CharField(max_length=32)
    mask_out     = md.CharField(max_length=32, blank=True)
    created_at   = md.DateTimeField(auto_now_add=True)
    updated_at   = md.DateTimeField(auto_now=True)

    class Meta:
        db_table      = 'problems'
        get_latest_by = 'created_at'

    @property
    def time_limit_in_secs(self):
        if self.time_limit % 1000 == 0:
            return self.time_limit // 1000
        else:
            return self.time_limit / 1000

    @time_limit_in_secs.setter
    def time_limit_in_secs(self, value):
        self.time_limit = int(value * 1000 + .5)

    def __str__(self):
        return self.name

    def clean(self):
        fields = (
            'description', 'input_specification', 'output_specification',
            'samples', 'explanations', 'notes', 'analysis',
        )
        for field, fmt in zip(fields, self.statements_format.split(',')):
            value = getattr(self, field)
            if value:
                value = pandoc.convert(value, fmt, to='html')
            setattr(self, field + '_html', value)


class ContestQuerySet(md.QuerySet):
    def privileged(self, user):
        return self if user.is_staff else self.filter(is_admin=False)


class Contest(md.Model):
    name                     = md.CharField(max_length=255)
    description              = md.TextField(blank=True)
    start_time               = md.DateTimeField(blank=True, null=True)
    duration                 = md.PositiveIntegerField(blank=True, null=True)
    freezing_time            = md.IntegerField(blank=True, null=True)
    is_school                = md.BooleanField()
    is_admin                 = md.BooleanField()
    is_training              = md.BooleanField()
    is_registration_required = md.BooleanField(default=False)
    is_unfrozen              = md.BooleanField(default=False)
    created_at               = md.DateTimeField(auto_now_add=True)
    updated_at               = md.DateTimeField(auto_now=True)
    problems                 = md.ManyToManyField(Problem, through='ProblemInContest')
    registered_users         = md.ManyToManyField(User, through='UserInContest')

    objects = ContestQuerySet.as_manager()

    class Meta:
        db_table      = 'contests'
        get_latest_by = 'created_at'

    @property
    def is_full_information_available(self):
        return self.is_training or timezone.now() >= self.start_time

    @property
    def finish_time(self):
        return self.start_time + timezone.timedelta(minutes=self.duration)

    @property
    def problem_count(self):
        return self.problem_in_contest_set.count()

    @property
    def duration_str(self):
        return '%d:%02d' % divmod(self.duration, 60)

    def __str__(self):
        return self.name if len(self.name) <= 70 else self.name[:67] + '...'

    def get_absolute_url(self):
        # TODO: Replace with something more appropriate.
        return reverse('contests:problem', args=[self.id, 1])

    def is_frozen_at(self, moment):
        if self.freezing_time is None:
            return False
        freezing_moment = self.start_time + timezone.timedelta(minutes=self.freezing_time)
        return freezing_moment <= moment and (moment < self.finish_time or not self.is_unfrozen)

    def get_due_time(self, unfrozen):
        now = timezone.now()
        if not unfrozen and self.is_frozen_at(now):
            return self.start_time + timezone.timedelta(minutes=self.freezing_time)
        else:
            return min(self.finish_time, now)

    def is_available_for(self, user):
        public = not self.is_registration_required
        return public or user.is_staff or (
            user.is_authenticated and self.registered_users.filter(id=user.id).exists()
        )

    @classmethod
    def three_way_split(cls, contests, threshold_time):
        """
        Splits the given iterable into three lists: actual, awaiting and past contests,
        regarding the given time point.
        """

        actual = []
        awaiting = []
        past = []
        for contest in contests:
            if contest.start_time > threshold_time:
                awaiting.append(contest)
            elif contest.finish_time <= threshold_time:
                past.append(contest)
            else:
                actual.append(contest)
        return actual, awaiting, past


class PICQuerySet(md.QuerySet):
    def is_visible(self, problem):
        return self.filter(
            md.Q(contest__is_training=True) | md.Q(contest__start_time__lte=timezone.now()),
            contest__is_admin=False,
            problem=problem,
        ).exists()


class ProblemInContest(md.Model):
    problem    = md.ForeignKey(Problem, md.PROTECT)
    contest    = md.ForeignKey(Contest, md.CASCADE)
    number     = md.PositiveIntegerField()
    score      = md.IntegerField(blank=True, null=True)
    # TODO: Remove this field.
    created_at = md.DateTimeField(auto_now_add=True)
    updated_at = md.DateTimeField(auto_now=True)

    objects = PICQuerySet.as_manager()

    class Meta:
        db_table             = 'problem_in_contests'
        default_related_name = 'problem_in_contest_set'
        verbose_name_plural  = 'problems in contest'
        get_latest_by        = 'created_at'

    def __str__(self):
        return '{0.contest.id:03}#{0.number}: "{0.problem}"'.format(self)

    def get_absolute_url(self):
        return reverse('contests:problem', args=[self.contest_id, self.number])

    @property
    def ordering_id(self):
        # ord('A') - 1 == 64
        return str(self.number) if self.contest.is_training else chr(self.number + 64)


class UserInContest(md.Model):
    user       = md.ForeignKey(User, md.CASCADE)
    contest    = md.ForeignKey(Contest, md.CASCADE)
    created_at = md.DateTimeField(auto_now_add=True)
    updated_at = md.DateTimeField(auto_now=True)

    class Meta:
        db_table             = 'user_in_contests'
        default_related_name = 'user_in_contest_set'
        verbose_name_plural  = 'users in contest'
        get_latest_by        = 'created_at'

    def __str__(self):
        return '{0.user} in {0.contest.id:03}'.format(self)


class ClarificationQuerySet(md.QuerySet):
    def privileged(self, user):
        return self if user.is_staff else self.filter(user=user)


class Clarification(md.Model):
    # TODO: Replace contest with problem_in_contest.
    contest     = md.ForeignKey(Contest, md.CASCADE, db_index=False)
    user        = md.ForeignKey(User, md.CASCADE, db_index=False)
    question    = md.TextField()
    format      = md.CharField(max_length=40,
        default='markdown',
        validators=[val.RegexValidator(r'^[^\s,]+$')])
    answer      = md.TextField(blank=True)
    answer_html = md.TextField(blank=True, editable=False)
    created_at  = md.DateTimeField(auto_now_add=True)
    updated_at  = md.DateTimeField(auto_now=True)

    objects = ClarificationQuerySet.as_manager()

    class Meta:
        db_table      = 'clarifications'
        get_latest_by = 'created_at'

    def has_answer(self):
        return bool(self.answer)

    has_answer.boolean = True

    def __str__(self):
        return self.question if len(self.question) <= 70 else self.question[:67] + '...'

    def clean(self):
        if self.has_answer():
            self.answer_html = pandoc.convert(self.answer, self.format, to='html')
        else:
            self.answer_html = ''


class NotificationQuerySet(md.QuerySet):
    def privileged(self, user):
        return self if user.is_staff else self.filter(visible=True, created_at__lte=timezone.now())


class Notification(md.Model):
    contest          = md.ForeignKey(Contest, md.CASCADE)
    format           = md.CharField(max_length=40,
        default='markdown',
        validators=[val.RegexValidator(r'^[^\s,]+$')])
    description      = md.TextField()
    description_html = md.TextField(editable=False)
    visible          = md.BooleanField(default=True)
    created_at       = md.DateTimeField(auto_now_add=True)
    updated_at       = md.DateTimeField(auto_now=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        db_table      = 'notifications'
        get_latest_by = 'created_at'

    def __str__(self):
        return self.description if len(self.description) <= 70 else self.description[:67] + '...'

    def clean(self):
        self.description_html = pandoc.convert(self.description, self.format, to='html')


class Compiler(md.Model):
    name            = md.CharField(max_length=64)
    codename        = md.CharField(max_length=32)
    runner_codename = md.CharField(max_length=32)
    obsolete        = md.BooleanField(default=False)
    # TODO: Remove this field when old tester support is dropped.
    extension       = md.CharField(max_length=255)
    created_at      = md.DateTimeField(auto_now_add=True)
    updated_at      = md.DateTimeField(auto_now=True)
    highlighter     = md.CharField(max_length=32)

    class Meta:
        db_table      = 'compilers'
        get_latest_by = 'created_at'

    def __str__(self):
        return self.name


class Attempt(md.Model):
    problem_in_contest = md.ForeignKey(ProblemInContest, md.CASCADE)
    user               = md.ForeignKey(User, md.CASCADE)
    source             = md.TextField()
    compiler           = md.ForeignKey(Compiler, md.CASCADE)
    time               = md.DateTimeField(auto_now_add=True)
    tester_name        = md.CharField(max_length=48, blank=True, default='')
    # TODO: SET NOT NULL.
    result             = md.CharField(max_length=36, blank=True, null=True, db_index=True)
    error_message      = md.TextField(blank=True, null=True) # NULL for optimization reason.
    # TODO: Make this field an integer (properly converting old attempts).
    used_time          = md.FloatField(blank=True, null=True)
    used_memory        = md.PositiveIntegerField(blank=True, null=True)
    checker_comment    = md.TextField(blank=True, default='')
    score              = md.FloatField(blank=True, null=True)
    # TODO: Remove this field.
    lock_version       = md.IntegerField(blank=True, null=True)
    created_at         = md.DateTimeField(auto_now_add=True)
    updated_at         = md.DateTimeField(auto_now=True)

    class Meta:
        db_table      = 'attempts'
        get_latest_by = 'time'

    @property
    def problem(self):
        return self.problem_in_contest.problem

    @property
    def contest(self):
        return self.problem_in_contest.contest

    @property
    def verdict(self):
        return self.result if self.score is None else '{0.score:.1f}%'.format(self)

    def __str__(self):
        return '[{0.id:05}/{0.problem.id:03}] {0.problem_in_contest} by {0.user}'.format(self)

    def get_absolute_url(self):
        return reverse('contests:attempt', args=[self.id])

    @staticmethod
    def encode_ejudge_verdict(result, score) -> (bytes, int):
        def parse_test(pos):
            try:
                return int(result[pos:])
            except (IndexError, ValueError):
                return 0

        # Sorted by popularity.
        if not result:  # But check for None first.
            return b'PD', 0
        if result.startswith('Wrong answer'):
            return b'WA', parse_test(21)
        if result.startswith('Time limit exceeded'):
            return b'TL', parse_test(28)
        if result.startswith('Runtime error'):
            return b'RT', parse_test(22)
        if result == 'Accepted' or (result == 'Tested' and score > 99.99):
            # FIXME: Number of passed tests should be returned.
            return b'OK', 0
        if result == 'Tested':
            # ditto
            return b'PT', 0
        if result.startswith('Memory limit exceeded'):
            return b'ML', parse_test(30)
        if result == 'Compilation error':
            return b'CE', 0
        if result.startswith('Presentation error'):
            return b'PE', parse_test(27)
        if result.startswith('Security violation'):
            return b'SE', parse_test(27)
        if result.startswith('Idleness limit exceeded'):
            return b'WT', parse_test(32)
        if result == 'Ignored':
            return b'IG', 0
        if result.startswith('Testing'):
            return b'RU', parse_test(11)
        if result in ('Queued', 'Compiling...'):
            return b'CG', 0
        if result.startswith('System error'):
            return b'CF', parse_test(21)
        return b'CF', 0


class TestInfo(md.Model):
    attempt         = md.ForeignKey(Attempt, md.CASCADE)
    test_number     = md.PositiveIntegerField()
    result          = md.CharField(max_length=23, blank=True, default='')
    # TODO: Maybe make these fields non-nullable? TestInfos are immutable anyway.
    used_memory     = md.PositiveIntegerField(blank=True, null=True)
    used_time       = md.FloatField(blank=True, null=True)
    checker_comment = md.TextField(blank=True, default='')

    class Meta:
        db_table        = 'test_infos'
        # unique_together = ('attempt_id', 'test_number')

    def __str__(self):
        return '{0.attempt_id:05}:{0.test_number}'.format(self)
