from django                      import forms
from django.contrib.auth.mixins  import LoginRequiredMixin
from django.core.exceptions      import PermissionDenied
from django.db                   import connection
from django.db.models            import F, Q, Func, CharField
from django.http                 import Http404
from django.shortcuts            import render, redirect
from django.utils                import timezone
from django.views.generic        import TemplateView, ListView

import collections
import os
import pygments.formatters
import pygments.lexers.special

from core.models  import Contest, ProblemInContest, Attempt, Compiler
from users.models import User, rank_users


class ContestIndexView(TemplateView):
    template_name = 'contests/contests.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # FIXME(nickolas): `LIMIT`.
        contests = (
            Contest
            .objects
            .privileged(self.request.user.is_staff)
            .filter(is_training=False)
            .order_by('-start_time')
        )

        actual, awaiting, past = Contest.three_way_split(contests, timezone.now())
        context.update(
            actual_contest_list=actual,
            wait_contest_list=awaiting,
            past_contest_list=past,
        )
        return context


class TrainingIndexView(TemplateView):
    template_name = 'contests/trainings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trainings_raw = (
            Contest
            .objects
            .privileged(self.request.user.is_staff)
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


class SelectContestMixin:
    def select_contest(self):
        if 'contest_id' not in self.kwargs:
            return None
        try:
            return (
                Contest
                .objects
                .privileged(self.request.user.is_staff)
                .get(id=self.kwargs['contest_id'])
            )
        except Contest.DoesNotExist:
            raise Http404('Не существует тренировки с запрошенным id.')


def get_time_info(contest):
    def seconds_to_str(seconds):
        hours, seconds = divmod(seconds, 3600)
        t_str = '%02d:%02d' % divmod(seconds, 60)
        if hours > 0:
            return '%d:' % hours + t_str
        return t_str

    if contest.is_training:
        return None
    TimeInfo = collections.namedtuple('TimeInfo', 'started finished time_str')
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

    return TimeInfo(started, finished, time_str)


class TrainingView(SelectContestMixin, TemplateView):
    template_name = 'contests/training.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        training = self.select_contest()
        time_info = get_time_info(training)
        pics = (
            ProblemInContest
            .objects
            .filter(contest=training)
            .order_by('number')
            .select_related('problem')
        )
        context.update(contest=training, pics=pics, time_info=time_info)
        return context


class ProblemView(TrainingView):
    template_name = 'contests/problem.html'

    # FIXME(nickolas): A lot of unused info is fetched.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        problem_number = self.kwargs['problem_number']
        problem = context['pics'].get(number=problem_number).problem
        context.update(problem=problem, problem_number=problem_number)
        return context


class SubmitForm(forms.Form):
    def __init__(self, contest, *args, **kwargs):
        super().__init__(*args, **kwargs)

        compilers = (
            Compiler
            .objects
            .filter(obsolete=False)
            .only('name')
            .order_by('name')
        )
        self.fields['compiler'] = forms.ChoiceField(
            choices=[(compiler.id, compiler.name) for compiler in compilers]
        )
        for compiler in compilers:
            if 'C++' in compiler.name: # Rather sensible default.
                self.initial['compiler'] = compiler.id
                break

        pics = (
            ProblemInContest
            .objects
            .filter(contest=contest)
            .select_related('problem')
            .only('number', 'problem__name')
            .order_by('number')
        )
        self.fields['problem'] = forms.ChoiceField(
            choices=[(pic.id, '%d. %s' % (pic.number, pic.problem.name)) for pic in pics],
        )

        self.fields['source'] = forms.CharField(widget=forms.Textarea)


class SubmitView(LoginRequiredMixin, SelectContestMixin, TemplateView):
    template_name = 'contests/submit.html'
    form_class = SubmitForm

    def get(self, request, **kwargs):
        contest = self.select_contest()
        time_info = get_time_info(contest)

        form = self.form_class(contest)
        return render(request, self.template_name, {'form': form, 'contest': contest, 'time_info': time_info})

    def post(self, request, **kwargs):
        contest = self.select_contest()
        time_info = get_time_info(contest)
        if time_info is not None:
            if not time_info.started:
                raise Http404('Соревнование ещё не началось')
            if time_info.finished:
                raise Http404('Соревнование уже завершилось')

        form = self.form_class(contest, request.POST)
        if form.is_valid():
            Attempt.objects.create(
                user=self.request.user,
                # TODO: Move object fetching to the form (if possible).
                problem_in_contest=ProblemInContest.objects.get(id=form.cleaned_data['problem']),
                compiler=Compiler.objects.get(id=form.cleaned_data['compiler']),
                source=form.cleaned_data['source'],
            )
            return redirect('contests:attempts', contest_id=contest.id)
        return render(request, self.template_name, {'form': form, 'contest': contest})


class AttemptsView(LoginRequiredMixin, SelectContestMixin, ListView):
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
        time_info = get_time_info(contest)
        context = super().get_context_data(**kwargs)
        context.update(contest=contest, time_info=time_info)
        return context


class AttemptDetailsView(LoginRequiredMixin, TemplateView):
    template_name = 'contests/source.html'

    def _find_lexer(self, name, **kwargs):
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

        lexer = self._find_lexer(attempt.compiler.highlighter, tabsize=4)
        formatter = pygments.formatters.HtmlFormatter(linenos='table', style='tango')
        context.update(
            contest=attempt.problem_in_contest.contest,
            attempt=attempt,
            highlighted_source=pygments.highlight(attempt.source, lexer, formatter),
            highlighting_styles=formatter.get_style_defs('.highlight'),
        )
        return context


class RatingView(SelectContestMixin, ListView):
    template_name = 'contests/rating.html'
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
        statuses = { }
        for user in users:
            statuses[user.id] = user.problems_status = pattern[:]

        tried = (
            Attempt
            .objects
            .filter(problem_in_contest__contest=contest_id)
            .exclude(
                Q(result__in=['', 'Queued', 'Compilation error', 'Ignored']) |
                Q(result__startswith='System error') |
                Q(result__startswith='Testing')
            )
            .extra(select={
                'succeeded': "result = 'Accepted' OR (result = 'Tested' AND attempts.score > 99.99)"
            })
            .distinct()
            .values_list('user', 'problem_in_contest__number', 'succeeded')
        )
        for user_id, number, succeeded in tried:
            try:
                status = statuses[user_id]
            except KeyError:
                pass # Skip users that don't have at least 1 accepted problem.
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
        context.update(contest=training, problems=problems)
        return context


class StandingsView(SelectContestMixin, TemplateView):
    template_name = 'contests/standings.html'

    def get_context_data(self, **kwargs):
        contest = self.select_contest()
        time_info = get_time_info(contest)

        now = timezone.now()
        internal_time = now - contest.start_time
        remaining_time_secs = max(60 * contest.duration - internal_time.total_seconds(), 0)
        finished = remaining_time_secs <= 0

        # TODO: add calculation for remaining_time_str

        # The time point we can see attempts until (either freezing or the end of the contest).
        if finished or contest.freezing_time is None:
            internal_due_time = contest.duration
        else:
            internal_due_time = contest.freezing_time
        due_time = min(contest.start_time + timezone.timedelta(minutes=internal_due_time), now)

        # TODO: add calculation for freezing_time_str

        problems = (
            ProblemInContest
            .objects
            .filter(contest=contest)
            # ord('A') - 1 == 64
            .annotate(number_char=Func(F('number') + 64, function='chr', output_field=CharField()))
            .order_by('number')
            .values('number_char', 'problem__name')
        )

        Result = collections.namedtuple('Result', 'status time')
        standings = collections.defaultdict(lambda: {
            # 'username': None,
            'score': 0,
            'penalty': 0,
            'results': [Result('.', None)] * len(problems),
        })

        statistics = []
        for problem in problems:
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
                    AND a.result NOT IN ('', 'Queued', 'Compilation error', 'Ignored')
                    AND a.result NOT LIKE 'Testing%%'
                    AND a.result NOT LIKE 'System error%%'
                    AND a.time <= %s
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
                    if statistic['first_accept'] is None or statistic['first_accept'] > accepted_time:
                        statistic['first_accept'] = accepted_time
                        statistic['first_accept_str'] = time_str
                    if statistic['last_accept'] is None or statistic['last_accept'] < accepted_time:
                        statistic['last_accept'] = accepted_time
                        statistic['last_accept_str'] = time_str
                else:
                    user_info['results'][problem_number] = Result('-%d' % attempt_count, None)
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
            problems=problems,
            standings=standings,
            statistics=statistics,
        )
        return context
