from django.utils import timezone

import collections


def get_relational_time_info(contest):
    def seconds_to_str(seconds):
        hours, seconds = divmod(seconds, 3600)
        t_str = '%02d:%02d' % divmod(seconds, 60)
        if hours > 0:
            return '%d:' % hours + t_str
        return t_str

    if contest.is_training:
        return None
    time_info = collections.namedtuple('TimeInfo', 'started finished time_str')
    now = timezone.now()
    finish_time = contest.start_time + timezone.timedelta(minutes=contest.duration)
    started = now >= contest.start_time
    finished = now >= finish_time
    if not started:
        seconds_till_start = int((contest.start_time - now).total_seconds())
        time_str = 'До начала соревнования осталось ' + seconds_to_str(seconds_till_start)
    elif finished:
        finish_time_local = timezone.localtime(finish_time)
        time_str = finish_time_local.strftime('Соревнование завершилось %d.%m.%y в %H:%M')
    else:
        seconds_till_finish = int((finish_time - now).total_seconds())
        time_str = 'До конца соревнования осталось ' + seconds_to_str(seconds_till_finish)

    return time_info(started, finished, time_str)
