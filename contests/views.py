import abc
import collections
import io
import os
import uuid
from   xml.sax import saxutils

from django.contrib.auth.mixins   import LoginRequiredMixin
from django.core.exceptions       import PermissionDenied
from django.db                    import connection
from django.db.models             import F, Q, BigIntegerField
from django.db.models.expressions import RawSQL
from django.db.models.functions   import Cast
from django.http                  import HttpResponse, Http404
from django.shortcuts             import render, redirect
from django.utils                 import timezone
from django.views.generic         import TemplateView, ListView, View
from django.views.generic.edit    import FormView
import pygments.formatters
import pygments.lexers.special

from contests.forms import SubmitForm, ClarificationForm
from contests.util  import get_relative_time_info
from core.models    import Contest, ProblemInContest, Notification, Clarification, Attempt, Compiler
from users.models   import User, rank_users


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


class ContestIndexView(TemplateView):
    template_name = 'contests/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # FIXME(nickolas): `LIMIT`.
        contests = (
            Contest
            .objects
            .privileged(self.request.user)
            .filter(is_training=False)
            .order_by('-start_time')
        )

        for contest in contests:
            contest.available = contest.is_available_for(self.request.user)

        actual, awaiting, past = Contest.three_way_split(contests, timezone.now())

        context.update(
            actual_contest_list=actual,
            wait_contest_list=awaiting,
            past_contest_list=past,
        )
        return context


class TrainingIndexView(TemplateView):
    template_name = 'contests/trainings/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trainings_raw = (
            Contest
            .objects
            .privileged(self.request.user)
            .filter(is_training=True)
            .order_by('name')
        )

        trainings = []
        cur_prefixes = []

        for t in trainings_raw:
            name_parts = t.name.split('/')

            # BUG(nickolas): Calling os.path.commonprefix on a [[str]] is an undocumented feature.
            # NOTE: os.path.commonprefix(['/usr/lib', '/usr/local/lib']) == '/usr/l'
            cur_prefixes = os.path.commonprefix([name_parts, cur_prefixes])
            idx = len(cur_prefixes)

            while idx < len(name_parts):
                if idx == len(name_parts) - 1:
                    trainings.append({
                        'tab': ' ' * idx,
                        'is_terminal': True,
                        'id': t.id,
                        'name': name_parts[idx]
                    })
                else:
                    cur_prefixes.append(name_parts[idx])
                    trainings.append({
                        'tab': ' ' * idx,
                        'is_terminal': False,
                        'id': None,
                        'name': name_parts[idx]
                    })
                idx += 1

        context['trainings'] = trainings
        return context


class TrainingView(SelectContestMixin, NotificationListMixin, TemplateView):
    template_name = 'contests/trainings/problems_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        training = self.select_contest()
        time_info = get_relative_time_info(training)
        pics = (
            ProblemInContest
            .objects
            .filter(contest=training)
            .order_by('number')
            .select_related('problem')
        )
        context.update(
            contest=training,
            pics=pics,
            time_info=time_info,
            notifications=self.get_notifications(training),
        )
        return context


class ProblemView(TrainingView):
    template_name = 'contests/problem.html'

    # FIXME(nickolas): A lot of unused info is fetched.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        problem_number = int(self.kwargs['problem_number'])
        problem = context['pics'].get(number=problem_number).problem
        context.update(problem=problem, problem_number=problem_number)
        return context


class SubmitView(LoginRequiredMixin, SelectContestMixin, NotificationListMixin, View):
    @staticmethod
    def _create_form(contest, initial_problem_number, *args, **kwargs):
        compilers = list(
            Compiler
            .objects
            .filter(obsolete=False)
            .only('name')
            .order_by('name')
        )
        pics = list(
            ProblemInContest
            .objects
            .filter(contest=contest)
            .select_related('problem')
            .only('number', 'problem__name')
            .order_by('number')
        )

        for compiler in compilers:
            if 'C++' in compiler.name:  # Rather sensible default.
                initial_compiler = compiler.id
                break
        else:
            initial_compiler = None

        try:
            initial_pic = pics[initial_problem_number].id
        except IndexError:
            initial_pic = None

        return SubmitForm(compilers, pics, initial_compiler, initial_pic, *args, **kwargs)

    def handle(self, request):
        contest = self.select_contest()
        time_info = get_relative_time_info(contest)
        available_for_user = contest.is_available_for(request.user)
        try:
            initial_problem_number = int(self.kwargs['problem_number']) - 1
        except (KeyError, ValueError):
            initial_problem_number = 0
        if request.method == 'POST':
            available = time_info is None or (time_info.started and not time_info.finished)
            form = self._create_form(contest, initial_problem_number, request.POST)
            if available and available_for_user and form.is_valid():
                form.submit(request.user)
                return redirect('contests:attempts', contest.id)
        else:
            form = self._create_form(contest, initial_problem_number)

        return render(request, 'contests/submit.html', {
            'form': form,
            'contest': contest,
            'time_info': time_info,
            'available': available_for_user,
            'notifications': self.get_notifications(contest),
        })

    def get(self, request, *args, **kwargs):
        return self.handle(request)

    post = get


class AttemptsView(LoginRequiredMixin, SelectContestMixin, NotificationListMixin, ListView):
    template_name = 'contests/attempts.html'
    context_object_name = 'attempts'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    # FIXME(nickolas): A contest is fetched twice.
    def get_queryset(self):
        contest = self.select_contest()
        attempts = (
            Attempt
            .objects
            .filter(problem_in_contest__contest=contest, user=self.request.user)
            .select_related('problem_in_contest__problem', 'compiler')
            .order_by('-created_at')
        )
        return attempts

    def get_context_data(self, **kwargs):
        contest = self.select_contest()
        time_info = get_relative_time_info(contest)
        context = super().get_context_data(**kwargs)
        context.update(
            contest=contest,
            time_info=time_info,
            notifications=self.get_notifications(contest),
        )
        return context


class AttemptDetailsView(LoginRequiredMixin, NotificationListMixin, TemplateView):
    template_name = 'contests/source.html'

    @staticmethod
    def _find_lexer(name, **kwargs):
        try:
            return pygments.lexers.get_lexer_by_name(name, **kwargs)
        except pygments.util.ClassNotFound:
            # TODO: Log that.
            return pygments.lexers.special.TextLexer(**kwargs)

    def get_context_data(self, **kwargs):
        attempt_id = self.kwargs['attempt_id']
        context = super().get_context_data(**kwargs)

        try:
            # A user can view their attempts in hidden contests,
            # if they manage to have ones, somehow.
            attempt = (
                Attempt
                .objects
                .select_related(
                    'compiler', 'problem_in_contest__problem', 'problem_in_contest__contest',
                )
                .get(id=attempt_id)
            )
        except Attempt.DoesNotExist:
            raise Http404('Не существует попытки с запрошенным id.')

        user = self.request.user
        # Compare IDs to avoid fetching attempt.user.
        if user.id != attempt.user_id and not user.is_staff:
            raise PermissionDenied('Вы не можете просматривать исходный код чужих посылок.')

        lexer = AttemptDetailsView._find_lexer(attempt.compiler.highlighter, tabsize=4)
        formatter = pygments.formatters.HtmlFormatter(linenos='table', style='tango')
        context.update(
            contest=attempt.problem_in_contest.contest,
            attempt=attempt,
            notifications=self.get_notifications(attempt.problem_in_contest.contest),
            highlighted_source=pygments.highlight(attempt.source, lexer, formatter),
            highlighting_styles=formatter.get_style_defs('.highlight'),
        )
        return context


class RatingView(SelectContestMixin, NotificationListMixin, ListView):
    template_name = 'contests/trainings/rating.html'
    context_object_name = 'user_list'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
        contest_id = self.kwargs['contest_id']
        users = list(
            User
            .objects
            .raw("""
                SELECT u.id, u.username, subq.problems_solved
                FROM (
                    SELECT id, COUNT(*) AS problems_solved, MAX(first_success) AS last_success
                    FROM (
                        SELECT u.id, MIN(a.created_at) AS first_success
                        FROM users u
                        JOIN attempts a ON a.user_id = u.id
                        JOIN problem_in_contests pic ON pic.id = a.problem_in_contest_id
                        WHERE pic.contest_id = %s
                        AND (a.result = 'Accepted' OR (a.result = 'Tested' AND a.score > 99.99))
                        GROUP BY u.id, a.problem_in_contest_id
                    ) subq
                    GROUP BY id
                ) subq
                JOIN users u ON u.id = subq.id
                ORDER BY subq.problems_solved DESC, subq.last_success
            """, [contest_id])
        )
        rank_users(users, 'problems_solved')
        pattern = ['.'] * ProblemInContest.objects.filter(contest=contest_id).count()
        statuses = {}
        for user in users:
            statuses[user.id] = user.problems_status = pattern[:]

        tried = (
            Attempt
            .objects
            .filter(problem_in_contest__contest=contest_id)
            .exclude(
                Q(result__in=['', 'Queued', 'Compiling...', 'Compilation error', 'Ignored']) |
                Q(result__startswith='System error') |
                Q(result__startswith='Testing')
            )
            .annotate(succeeded=RawSQL(
                "result = 'Accepted' OR (result = 'Tested' AND attempts.score > 99.99)",
                (),
            ))
            .distinct()
            .values_list('user', 'problem_in_contest__number', 'succeeded')
        )
        for user_id, number, succeeded in tried:
            try:
                status = statuses[user_id]
            except KeyError:
                pass  # Skip users that don't have at least 1 accepted problem.
            else:
                if succeeded:
                    status[number - 1] = '+'
                elif status[number - 1] != '+':
                    status[number - 1] = '-'

        return users

    def get_context_data(self, **kwargs):
        training = self.select_contest()
        problems = (
            ProblemInContest
            .objects
            .filter(contest=training)
            .select_related('problem')
            .only('number', 'problem__name')
            .order_by('number')
        )

        context = super().get_context_data(**kwargs)
        context.update(
            contest=training,
            problems=problems,
            notifications=self.get_notifications(training),
        )
        return context


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

        result = collections.namedtuple('Result', 'status time')
        standings = collections.defaultdict(lambda: {
            # 'username': None,
            'score': 0,
            'penalty': 0,
            'results': [result('.', None)] * len(problems),
        })

        statistics = []
        for _ in problems:
            statistics.append({
                'total_runs': 0,
                'accepted': 0,
                'rejected': 0,
                'first_accept': None,
                'first_accept_str': '',
                'last_accept': None,
                'last_accept_str': '',
            })

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
                    user_info['results'][problem_number] = result(status, time_str)
                    statistic['accepted'] += 1
                    statistic['rejected'] += attempt_count - 1
                    if statistic['first_accept'] is None or statistic['first_accept'] > accepted_time:
                        statistic['first_accept'] = accepted_time
                        statistic['first_accept_str'] = time_str
                    if statistic['last_accept'] is None or statistic['last_accept'] < accepted_time:
                        statistic['last_accept'] = accepted_time
                        statistic['last_accept_str'] = time_str
                else:
                    user_info['results'][problem_number] = result('-%d' % attempt_count, None)
                    statistic['rejected'] += attempt_count

        names = (
            User
            .objects
            .filter(id__in=standings)
            .values_list('id', 'username')
        )
        for user_id, username in names:
            standings[user_id]['username'] = username

        # TODO: Last submit time.
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


class BaseXMLStandingsView(StandingsDueTimeMixinABC, SelectContestMixin, View):
    @staticmethod
    def _encode_datetime(moment):
        return timezone.localtime(moment).strftime('%Y/%m/%d %H:%M:%S').encode()

    # TODO: use is_staff mixin instead, when it is ready
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404('Не существует запрошенной страницы')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, contest_id, *args, **kwargs):
        contest = self.select_contest()
        if contest.is_training:
            raise Http404
        pics = (
            ProblemInContest
            .objects
            .filter(contest=contest_id)
            .annotate_with_number_char()
            .order_by('number')
            .values_list('id', 'number_char', 'problem__name')
        )
        attempts = (
            Attempt
            .objects
            .filter(
                problem_in_contest__in=[pic_id for pic_id, number_char, name in pics],
                time__lt=self.get_due_time(contest),
            )
            .annotate(
                submit_time_sec=RawSQL('extract(epoch FROM time - %s)', [contest.start_time]),
                time_ns=Cast(F('used_time') * 1000000000 + 0.5, BigIntegerField()),
            )
            # .order_by('time')
            .values_list(
                'id', 'submit_time_sec', 'result', 'score', 'time_ns',
                'user', 'user__username',
                'problem_in_contest',
                'compiler', 'compiler__codename', 'compiler__name',
            )
        )
        users = { }
        compilers = { }
        a = io.BytesIO()
        # We generate XML "by hand" for extra speed.
        for (attempt_id, submit_time_sec, result, score, time_ns, user_id, username, pic_id,
            compiler_id, codename, compiler_name) in attempts:

            users[user_id] = username
            compilers[compiler_id] = (codename, compiler_name)
            status, test = Attempt.encode_ejudge_verdict(result, score)
            a.write(
                b'<run run_id="%d" time="%d"'
                b' user_id="%d" prob_id="%d" lang_id="%d" status="%s" test="%d"'
                b' nsec="%d" run_uuid="%s" passed_mode="yes"/>' % (
                    attempt_id, submit_time_sec,
                    user_id, pic_id, compiler_id, status, test,
                    time_ns or 0, str(uuid.uuid4()).encode(),
                )
            )

        r = HttpResponse(content_type='application/xml')
        r.write(
            b'<?xml version="1.0" encoding="utf-8"?>'
            b'<runlog contest_id="%s" duration="%d" fog_time="%d"'
            b' start_time="%s" stop_time="%s" current_time="%s">'
            b'<name>%s</name>'
            b'<users>' % (
                contest_id.encode(),
                contest.duration * 60,
                contest.freezing_time * 60,
                self._encode_datetime(contest.start_time),
                self._encode_datetime(contest.finish_time),
                self._encode_datetime(timezone.now()),
                saxutils.escape(contest.name).encode(),
            )
        )
        for user_id, username in users.items():
            r.write(b'<user id="%d" name=%s/>' % (user_id, saxutils.quoteattr(username).encode()))
        r.write(b'</users><problems>')
        for pic_id, number_char, name in pics:
            r.write(b'<problem id="%d" short_name="%c" long_name=%s/>' % (
                pic_id, number_char.encode(), saxutils.quoteattr(name).encode(),
            ))
        r.write(b'</problems><languages>')
        for compiler_id, (codename, name) in compilers.items():
            r.write(
                b'<language id="%d" short_name=%s long_name=%s/>' % (
                compiler_id,
                saxutils.quoteattr(codename).encode(),
                saxutils.quoteattr(name).encode(),
            ))
        r.write(b'</languages><runs>')
        r.write(a.getvalue())
        r.write(b'</runs></runlog>')
        return r


class XMLStandingsView(StandingsDueTimeMixin, BaseXMLStandingsView):
    pass


class UnfrozenXMLStandingsView(UnfrozenStandingsDueTimeMixin, BaseXMLStandingsView):
    pass


class ClarificationsView(LoginRequiredMixin, SelectContestMixin, NotificationListMixin, FormView):
    template_name = 'contests/clarifications.html'
    form_class = ClarificationForm

    def get_context_data(self, **kwargs):
        contest = self.select_contest()
        context = super().get_context_data(**kwargs)
        context.update(
            contest=contest,
            time_info=get_relative_time_info(contest),
            notifications=self.get_notifications(contest),
            clarifications=(
                Clarification
                .objects
                .privileged(self.request.user)
                .filter(contest=contest)
                .order_by('-created_at')
            ),
        )
        return context

    def form_valid(self, form):
        contest = self.select_contest()
        time_info = get_relative_time_info(contest)
        if time_info is None or time_info.started:
            form.ask(self.request.user, contest)
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.get_full_path()
