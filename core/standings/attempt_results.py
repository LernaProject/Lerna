import abc

from core.util import format_time


class AttemptResult(abc.ABC):
    def __init__(self, user_id, problem_number, score):
        assert -1e-6 < score < 1 + 1e-6, "Invalid %s's score: %f" % (type(self).__name__, score)
        self.user_id = user_id
        self.problem_number = problem_number
        self.score = min(max(0, score), 1)

    @property
    def accepted(self):
        return self.score > .9999

    @property
    def rejected(self):
        return self.score < .0001

    def describe(self, usernames, pics):
        return '{0}, "{1.ordering_id}. {1.problem.name}"'.format(
            usernames[self.user_id], pics[self.problem_number],
        )

    @abc.abstractmethod
    def __str__(self):
        pass


class _CountedMixin:
    def __init__(self, count, *args, **kwargs):
        assert count > 0, "Invalid %s's count: %s" % (type(self).__name__, count)
        self.count = count
        super().__init__(*args, **kwargs)


class TimedMixin:
    def __init__(self, time, contest_start_time, *args, **kwargs):
        assert time is not None, "%s's time must not be None" % type(self).__name__
        self.time = time
        self.minutes = int((time - contest_start_time).total_seconds()) // 60
        super().__init__(*args, **kwargs)

    def describe(self, usernames, pics):
        return super().describe(usernames, pics) + ', ' + format_time(self.minutes)

    def __str__(self):
        return super().__str__() + '\n' + format_time(self.minutes)


class AcmTrainingAttemptResult(AttemptResult):
    def __init__(self, user_id, problem_number, accepted):
        super().__init__(user_id, problem_number, bool(accepted))

    def __str__(self):
        return '\u2012+'[self.accepted]


class AcmAttemptResult(_CountedMixin, AcmTrainingAttemptResult):
    def __init__(self, user_id, problem_number, accepted, count):
        super().__init__(count, user_id, problem_number, accepted)

    @property
    def status(self):
        if self.accepted:
            return '+' if self.count == 1 else '+%d' % (self.count - 1)
        else:
            return '\u2012%d' % self.count

    def describe(self, usernames, pics):
        return super().describe(usernames, pics) + ', ' + self.status

    def __str__(self):
        return self.status


class TimedAcmAttemptResult(TimedMixin, AcmAttemptResult):
    def __init__(self, user_id, problem_number, accepted, count, time, contest_start_time):
        super().__init__(time, contest_start_time, user_id, problem_number, accepted, count)


class KirovTrainingAttemptResult(AttemptResult):
    @property
    def percentage(self):
        result = '%.1f' % (self.score * 100)
        return (result[:-2] if result[-1] == '0' else result) + '%'

    def describe(self, usernames, pics):
        return super().describe(usernames, pics) + ', ' + self.percentage

    def __str__(self):
        return self.percentage


class KirovAttemptResult(_CountedMixin, KirovTrainingAttemptResult):
    def __init__(self, user_id, problem_number, score, count):
        super().__init__(count, user_id, problem_number, score)

    def __str__(self):
        return '{0.percentage}\n({0.count})'.format(self)


class TimedKirovAttemptResult(TimedMixin, KirovAttemptResult):
    def __init__(self, user_id, problem_number, score, count, time, contest_start_time):
        super().__init__(time, contest_start_time, user_id, problem_number, score, count)
