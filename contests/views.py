from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts           import render, redirect
from django.core.exceptions     import PermissionDenied
from django.http                import Http404
from django.views.generic       import TemplateView, ListView
from django.views.generic.edit  import FormView
from django                     import forms
from django.db.models           import Count, Q

import datetime
import os

from core.models import Contest, ProblemInContest, Attempt, Compiler
from users.models import User, rank_users

from operator import itemgetter

class ContestIndexView(TemplateView):
    template_name = 'contests/contests.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contests = (
            Contest
            .objects
            .filter(is_training=False)
            .order_by('-start_time')
        )

        if not self.request.user.is_staff:
            contests = contests.filter(is_admin=False)

        now = datetime.datetime.now()
        actual, awaiting, past = Contest.three_way_split(contests, now)
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
            .filter(is_training=True)
            .order_by('name')
        )

        if not self.request.user.is_staff:
            trainings_raw = trainings_raw.filter(is_admin=False)

        trainings = []
        cur_prefixes = []

        for t in trainings_raw:
            name_parts = t.name.split('/')

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


class TrainingView(TemplateView):
    template_name = 'contests/training.html'

    def get_context_data(self, *, contest_id, **kwargs):
        context = super().get_context_data(id=contest_id, **kwargs)

        if not Contest.objects.filter(id=contest_id).exists():
            raise Http404("Не существует тренировки с запрошенным id.")

        training = Contest.objects.get(id=contest_id)
        if not training.is_training:
            raise Http404("Не существует тренировки с запрошенным id.")

        user = self.request.user
        if training.is_admin and not user.is_staff:
            raise Http404("Не существует тренировки с запрошенным id.")

        pics = (
            ProblemInContest
            .objects
            .filter(contest=training)
            .order_by('number')
            .select_related('problem')
        )
        context.update(contest=training, pics=pics)
        return context


class ProblemView(TrainingView):
    template_name = 'contests/problem.html'

    def get_context_data(self, *, contest_id, **kwargs):
        context = super().get_context_data(contest_id=contest_id, **kwargs)
        problem_number = self.kwargs['problem_number']
        problem = context['pics'].get(number=problem_number).problem
        context.update(problem=problem, problem_number=problem_number)
        return context


class SubmitForm(forms.Form):
    def __init__(self, contest_id, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['compiler'] = forms.ChoiceField(
            choices=[(compiler.id, compiler.name) for compiler in Compiler.objects.all().exclude(obsolete=True)]
        )

        contest = Contest.objects.get(id=contest_id)
        pics = (
            ProblemInContest
            .objects
            .filter(contest=contest)
            .order_by('number')
            .select_related('problem')
        )
        self.fields['problem'] = forms.ChoiceField(
            choices=[(pic.id, '{0} {1}'.format(pic.number, pic.problem.name)) for pic in pics]
        )

        self.fields['source'] = forms.CharField(widget=forms.Textarea)


class SubmitView(LoginRequiredMixin, FormView):
    template_name = 'contests/submit.html'
    form_class = SubmitForm

    def get(self, request, contest_id, *args, **kwargs):
        contest = Contest.objects.get(id=contest_id)
        form = self.form_class(contest_id)
        return render(request, self.template_name, {'form': form, 'contest': contest})

    def post(self, request, contest_id, *args, **kwargs):
        contest = Contest.objects.get(id=contest_id)
        form = self.form_class(contest_id, request.POST)
        if form.is_valid():
            Attempt.objects.create(
                user=self.request.user,
                # TODO: Move object fetching to the form (if possible).
                problem_in_contest=ProblemInContest.objects.get(id=form.cleaned_data['problem']),
                compiler=Compiler.objects.get(id=form.cleaned_data['compiler']),
                source=form.cleaned_data['source'],
            )
            return redirect('contests:attempts', contest_id=contest_id)
        return render(request, self.template_name, {'form': form, 'contest': contest})


class AttemptsView(LoginRequiredMixin, ListView):
    template_name = 'contests/attempts.html'
    context_object_name = 'attempts'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
        contest = Contest.objects.get(id=self.kwargs['contest_id'])
        user = self.request.user
        attempts = (
            Attempt
            .objects
            .filter(problem_in_contest__contest=contest, user=user)
            .select_related('problem_in_contest', 'compiler')
            .order_by('-created_at')
        )
        return attempts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contest_id = self.kwargs['contest_id']

        if not Contest.objects.filter(id=contest_id).exists():
            raise Http404("Не существует тренировки с запрошенным id.")

        contest = Contest.objects.get(id=contest_id)

        user = self.request.user
        if contest.is_admin and not user.is_staff:
            raise Http404("Не существует тренировки с запрошенным id.")

        context.update(contest=contest)
        return context


class AttemptDetailsView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, *, attempt_id, **kwargs):
        context = super().get_context_data(id=attempt_id, **kwargs)

        if not Attempt.objects.filter(id=attempt_id).exists():
            raise Http404("Не существует попытки с запрошенным id.")

        attempt = Attempt.objects.get(id=attempt_id)
        contest = attempt.problem_in_contest.contest

        user = self.request.user
        if user.id != attempt.user_id and not user.is_staff:
            raise PermissionDenied('Вы не можете просматривать исходный код чужих посылок.')

        context.update(contest=contest, attempt=attempt)
        return context


class SourceView(AttemptDetailsView):
    template_name = 'contests/source.html'


class ErrorsView(AttemptDetailsView):
    template_name = 'contests/errors.html'


class RatingView(ListView):
    template_name = 'contests/rating.html'
    context_object_name = 'user_list'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
        contest = Contest.objects.get(id=self.kwargs['contest_id'])
        users = (
            User
            .objects
            .filter(
                Q(attempt__problem_in_contest__contest_id=contest.id),
                Q(attempt__result='Accepted') | Q(attempt__result='Tested', attempt__score__gt=99.99),
            )
            .annotate(problems_solved=Count('attempt__problem_in_contest__problem', distinct=True))
            .order_by('-problems_solved')
        )
        rank_users(users, 'problems_solved')

        problems = (
            ProblemInContest
            .objects
            .filter(
                contest_id=contest.id
            )
        )
        # TODO: выбирать все поптыки одним запросом, как для standings
        for user in users:
            solved = (
                ProblemInContest
                .objects
                .filter(
                    Q(attempt__problem_in_contest__contest_id=contest.id),
                    Q(attempt__result='Accepted') | Q(attempt__result='Tested', attempt__score__gt=99.99),
                    Q(attempt__user=user)
                )
            )
            # TODO: не учитывать попытки со статусами SE, Ignored, Testing ..., ''
            tried = (
                ProblemInContest
                .objects
                .filter(
                    attempt__problem_in_contest__contest_id=contest.id,
                    attempt__user=user
                )
            )
            problems_status = ['.'] * len(problems)
            for problem in problems:
                if problem in solved:
                    problems_status[problem.number - 1] = '+'
                elif problem in tried:
                    problems_status[problem.number - 1] = '-'
            user.problems_status = problems_status

        return users

    def get_context_data(self, **kwargs):
        contest_id = self.kwargs['contest_id']
        if not Contest.objects.filter(id=contest_id).exists():
            raise Http404("Не существует тренировки с запрошенным id.")

        training = Contest.objects.get(id=contest_id)
        if not training.is_training:
            raise Http404("Не существует тренировки с запрошенным id.")

        user = self.request.user
        if training.is_admin and not user.is_staff:
            raise Http404("Не существует тренировки с запрошенным id.")

        problems = (
            ProblemInContest
            .objects
            .filter(
                contest_id=contest_id
            )
            .order_by('number')
        )
        context = super().get_context_data(**kwargs)
        context.update(contest=training, problems=problems)
        return context


class StandingsView(TemplateView):
    template_name = 'contests/standings.html'

    def get_context_data(self, **kwargs):
        contest_id = self.kwargs['contest_id']
        if not Contest.objects.filter(id=contest_id).exists():
            raise Http404("Не существует контеста с запрошенным id.")

        contest = Contest.objects.get(id=contest_id)
        if contest.is_training:
            raise Http404("Не существует контеста с запрошенным id.")

        user = self.request.user
        if contest.is_admin and not user.is_staff:
            raise Http404("Не существует контеста с запрошенным id.")

        now = datetime.datetime.now()
        inner_time = now - contest.start_time
        time_before_end = 60 * contest.duration - inner_time.seconds
        finished = time_before_end < 0

        # TODO: add calculation for time_before_end_str

        # время, вплоть до которого мы просматриваем попытки (до заморозки или до конца контеста, если таковой нет)
        if finished or contest.freezing_time is None:
            inner_up_time = contest.duration
        else:
            inner_up_time = contest.freezing_time
        up_time = contest.start_time + datetime.timedelta(minutes=inner_up_time)
        if now < up_time:
            up_time = now

        # TODO: add calculation for freezing_time_str

        problems = (
            ProblemInContest
            .objects
            .filter(
                contest_id=contest.id
            )
        )
        for problem in problems:
            problem.number_char = chr(ord('A') + problem.number - 1)

        attempts = (
            Attempt
            .objects
            .filter(
                Q(problem_in_contest__contest_id=contest.id),
                Q(time__gte=contest.start_time)
            )
            .exclude(
                Q(result__in=('Compilation error', 'Ignored', '')) or
                Q(result__startswith='Testing') or
                Q(result__startswith='System error') or
                Q(time__gt=up_time)
            )
            .order_by('time')
        )

        prepared_attempts = {}
        for attempt in attempts:
            if attempt.user_id not in prepared_attempts:
                prepared_attempts[attempt.user_id] = {}
            if attempt.problem_in_contest.number not in prepared_attempts[attempt.user_id]:
                prepared_attempts[attempt.user_id][attempt.problem_in_contest.number] = []
            prepared_attempts[attempt.user_id][attempt.problem_in_contest.number].append(attempt)
        users = (
            User
            .objects
            .filter(
                Q(id__in=prepared_attempts.keys())
            )
        )

        standings = []
        for user in users:
            user_info = {'user': user,
                         'sum': 0,
                         'fine_time': 0,
                         'results': [{'status': '.', 'time': None}] * len(problems)}
            for problem_number, problem_attempts in prepared_attempts[user.id].items():
                fail_attempts_count = 0
                accepted_time = None
                for attempt in problem_attempts:
                    if attempt.result == 'Accepted':
                        accepted_time = attempt.time
                        break
                    else:
                        fail_attempts_count += 1

                number = int(problem_number) - 1
                if accepted_time:
                    user_info['sum'] += 1

                    status = "+{0}".format(fail_attempts_count) if fail_attempts_count else '+'
                    accepted_time = (accepted_time - contest.start_time).seconds // 60
                    time = "{0}:{1:02}".format(accepted_time // 60, accepted_time % 60)

                    user_info['results'][number] = {'status': status, 'time': time}
                    user_info['fine_time'] += accepted_time + 20 * fail_attempts_count
                elif fail_attempts_count:
                    user_info['results'][number] = {'status': -fail_attempts_count, 'time': None}

            standings.append(user_info)

            standings.sort(key=itemgetter('fine_time'))
            standings.sort(key=itemgetter('sum'), reverse=True)

            rank = 0
            for user_info in standings:
                rank += 1
                user_info['rank'] = rank

        context = super().get_context_data(**kwargs)
        context.update(contest=contest, problems=problems, standings=standings,
                       now=now,
                       inner_time=inner_time,
                       inner_up_time=inner_up_time,
                       up_time=up_time,
                       prepared_attempts=prepared_attempts,
                       users=users
                       )
        return context