import collections
import datetime

from django.db            import connection
from django.http          import Http404
from django.utils         import timezone
from django.views.generic import TemplateView

from .util import (
    NotificationListMixin, SelectContestMixin, StandingsDueTimeMixinABC,
    StandingsDueTimeMixin, UnfrozenStandingsDueTimeMixin, get_relative_time_info,
)
from core.models  import Attempt, ProblemInContest
from users.models import User


class BaseStandingsView(StandingsDueTimeMixinABC, SelectContestMixin, NotificationListMixin, TemplateView):
    template_name = 'contests/rating.html'

    def get_context_data(self, **kwargs):
        contest = self.select_contest()
        time_info = get_relative_time_info(contest)

        # The time point we can see attempts until (either freezing or the end of the contest).
        due_time = self.get_due_time(contest)

        problems = (
            ProblemInContest
            .objects
            .filter(contest=contest)
            .order_by('number')
            .values('number', 'problem__name')
        )

        Result = collections.namedtuple('Result', 'status time')
        standings = collections.defaultdict(lambda: {
            # 'username': None,
            'score': 0,
            'penalty': 0,
            'results': [Result('.', None)] * len(problems),
        })

        statistics = []
        for _ in problems:
            statistics.append({
                'total_runs': 0,
                'accepted': 0,
                'rejected': 0,
                'first_accepted': 1 << 63,
                'first_accepted_str': '',
                'last_accepted': -1 << 63,
                'last_accepted_str': '',
            })

        last_accepted = {
            # 'user_id': None,
            # 'number': None,
            'time': datetime.datetime(1970, 1, 1, tzinfo=timezone.get_default_timezone()),
            # 'username': None,
            # 'problem_name': None,
            # 'time_str': None,
        }
        # Create the table.
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH all_attempts AS (
                    SELECT u.id AS user_id,
                        pic.number AS num,
                        a.time,
                        a.result = 'Accepted' AS succeeded
                    FROM users u
                    JOIN attempts a ON a.user_id = u.id
                    JOIN problem_in_contests pic ON pic.id = a.problem_in_contest_id
                    WHERE pic.contest_id = %s
                    AND a.result NOT IN ('', 'Queued', 'Compiling...', 'Compilation error', 'Ignored')
                    AND a.result NOT LIKE 'Testing%%'
                    AND a.result NOT LIKE 'System error%%'
                    AND a.time < %s
                )
                SELECT a.user_id, a.num - 1, COUNT(*), ok.succeeded_at
                FROM all_attempts a
                LEFT JOIN (
                    SELECT user_id, num, MIN("time") AS succeeded_at
                    FROM all_attempts
                    WHERE succeeded
                    GROUP BY user_id, num
                ) ok ON ok.user_id = a.user_id AND ok.num = a.num
                WHERE ok.succeeded_at IS NULL
                OR a.time <= ok.succeeded_at
                GROUP BY a.user_id, a.num, ok.succeeded_at
            """, [contest.id, due_time])

            for user_id, problem_number, attempt_count, succeeded_at in cursor:
                user_info = standings[user_id]
                statistic = statistics[problem_number]
                statistic['total_runs'] += attempt_count
                if succeeded_at is not None:
                    accepted_time = int((succeeded_at - contest.start_time).total_seconds() / 60)
                    time_str = '%d:%02d' % divmod(accepted_time, 60)
                    status = '+' if attempt_count == 1 else '+%d' % (attempt_count - 1)

                    user_info['score'] += 1
                    user_info['penalty'] += accepted_time + (attempt_count - 1) * 20
                    user_info['results'][problem_number] = Result(status, time_str)

                    statistic['accepted'] += 1
                    statistic['rejected'] += attempt_count - 1
                    if accepted_time < statistic['first_accepted']:
                        statistic['first_accepted'] = accepted_time
                        statistic['first_accepted_str'] = time_str
                    if accepted_time > statistic['last_accepted']:
                        statistic['last_accepted'] = accepted_time
                        statistic['last_accepted_str'] = time_str
                    if succeeded_at > last_accepted['time']:
                        last_accepted = {
                            'user_id': user_id,
                            'number': problem_number,
                            'time': succeeded_at,
                            # 'username': None,
                            # 'problem_name': None,
                            # 'time_str': None,
                        }
                else:
                    user_info['results'][problem_number] = Result('-%d' % attempt_count, None)
                    statistic['rejected'] += attempt_count

        # Calculate the last accepted and last submitted attempts.
        if 'number' in last_accepted:
            time = int((last_accepted['time'] - contest.start_time).total_seconds() / 60)
            last_accepted['problem_name'] = problems[last_accepted['number']]['problem__name']
            last_accepted['number'] += 1
            last_accepted['time_str'] = '%d:%02d' % divmod(time, 60)
            last_accepted_user_id = last_accepted['user_id']
        else:
            last_accepted = last_accepted_user_id = None
        try:
            last_submitted = (
                Attempt
                .objects
                .filter(problem_in_contest__contest=contest, time__lt=due_time)
                .exclude(result__in=['', 'Queued', 'Compiling...', 'Compilation error', 'Ignored'])
                .exclude(result__startswith='Testing')
                .exclude(result__startswith='System error')
                .select_related('user', 'problem_in_contest__problem')
                .only(
                    'time', 'user__username',
                    'problem_in_contest__number', 'problem_in_contest__problem__name',
                )
                .latest()
            )
        except Attempt.DoesNotExist:
            last_submitted = None
        else:
            time = int((last_submitted.time - contest.start_time).total_seconds() / 60)
            last_submitted = {
                'user_id': last_submitted.user.id,
                'number': last_submitted.problem_in_contest.number,
                'time': last_submitted.time,
                'username': last_submitted.user.username,
                'problem_name': last_submitted.problem_in_contest.problem.name,
                'time_str': '%d:%02d' % divmod(time, 60),
            }

        # Populate data with user names.
        names = (
            User
            .objects
            .filter(id__in=standings)
            .values_list('id', 'username')
        )
        for user_id, username in names:
            standings[user_id]['username'] = username
            if user_id == last_accepted_user_id:
                last_accepted['username'] = username

        # Sort the table and assign ranks.
        standings = sorted(standings.values(), key=lambda info: (-info['score'], info['penalty']))
        for rank, user_info in enumerate(standings, 1):
            user_info['rank'] = rank

        context = super().get_context_data(**kwargs)
        context.update(
            contest=contest,
            time_info=time_info,
            available=contest.is_available_for(self.request.user),
            problems=problems,
            notifications=self.get_notifications(contest),
            standings=standings,
            statistics=statistics,
            last_attempts=(last_accepted, last_submitted),
        )
        return context


class StandingsView(StandingsDueTimeMixin, BaseStandingsView):
    pass


class UnfrozenStandingsView(UnfrozenStandingsDueTimeMixin, BaseStandingsView):
    # TODO: use is_staff mixin instead, when it is ready
    def dispath(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404('Не существует запрошенной страницы')
        return super().dispath(request, *args, **kwargs)
