import abc
import collections

from django.http  import Http404
from django.utils import timezone

from core.models import Contest, Notification


TimeInfo = collections.namedtuple('TimeInfo', 'started finished frozen time_str freezing_time_str')


def get_relative_time_info(contest):
    def seconds_to_str(seconds):
        hours, seconds = divmod(seconds, 3600)
        t_str = '%02d:%02d' % divmod(seconds, 60)
        if hours > 0:
            return '%d:' % hours + t_str
        return t_str

    if contest.is_training:
        return None
    now = timezone.now()
    started = now >= contest.start_time
    finished = now >= contest.finish_time
    if not started:
        seconds_till_start = int((contest.start_time - now).total_seconds())
        time_str = 'До начала соревнования осталось ' + seconds_to_str(seconds_till_start)
    elif finished:
        finish_time_local = timezone.localtime(contest.finish_time)
        time_str = finish_time_local.strftime('Соревнование завершилось %d.%m.%y в %H:%M')
    else:
        seconds_till_finish = int((contest.finish_time - now).total_seconds())
        time_str = 'До конца соревнования осталось ' + seconds_to_str(seconds_till_finish)

    frozen = False
    freezing_time_str = None
    if started and contest.freezing_time is not None:
        frozen = contest.is_frozen_at(now)
        if frozen:
            freezing_time_str = 'Таблица результатов заморожена'
        elif now >= contest.finish_time:
            freezing_time_str = 'Таблица результатов разморожена'
        else:
            freezing_time = contest.start_time + timezone.timedelta(minutes=contest.freezing_time)
            seconds_till_freezing = int((freezing_time - now).total_seconds())
            freezing_time_str = 'До заморозки таблицы результатов осталось ' + seconds_to_str(seconds_till_freezing)

    return TimeInfo(started, finished, frozen, time_str, freezing_time_str)


class NotificationListMixin:
    def get_notifications(self, contest):
        return (
            Notification
            .objects
            .privileged(self.request.user)
            .filter(contest=contest)
            .order_by('-created_at')
        )


class SelectContestMixin:
    def select_contest(self):
        try:
            return (
                Contest
                .objects
                .privileged(self.request.user)
                .get(id=self.kwargs['contest_id'])
            )
        except Contest.DoesNotExist:
            raise Http404('Не существует тренировки с запрошенным id.')


class StandingsDueTimeMixinABC(abc.ABC):
    @abc.abstractmethod
    def get_due_time(self, contest):
        pass


class StandingsDueTimeMixin:
    @staticmethod
    def get_due_time(contest):
        now = timezone.now()
        if contest.is_frozen_at(now):
            return contest.start_time + timezone.timedelta(minutes=contest.freezing_time)
        else:
            return min(contest.finish_time, now)


class UnfrozenStandingsDueTimeMixin:
    @staticmethod
    def get_due_time(contest):
        return min(contest.finish_time, timezone.now())
