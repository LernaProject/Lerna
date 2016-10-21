from django.shortcuts          import get_object_or_404, render, redirect
from django.views.generic      import TemplateView, ListView
from django.views.generic.edit import FormView
from django                    import conf, forms

import datetime
import os
import pytz

from core.models import Contest, ProblemInContest, Attempt, Compiler


class ContestIndexView(TemplateView):
    template_name = 'contests/contests.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contests = (
            Contest
            .objects
            .filter(is_training=False)
        )
        now = datetime.datetime.now(pytz.timezone(conf.settings.TIME_ZONE))
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
        training = Contest.objects.get(id=contest_id)
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
            choices=[(compiler.id, compiler.name) for compiler in Compiler.objects.all()]
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


class SubmitView(FormView):
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
                problem_in_contest=form.cleaned_data['problem'],
                compiler=form.cleaned_data['compiler'],
                source=form.cleaned_data['source'],
            )
            return redirect('contests:attempts', contest=contest_id)
        return render(request, self.template_name, {'form': form, 'contest': contest})


class AttemptsView(ListView):
    template_name = 'contests/attempts.html'
    context_object_name = 'attempts'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
        contest = Contest.objects.get(id=self.kwargs['contest_id'])
        attempts = None
        if self.request.user.is_authenticated():
            attempts = (
                Attempt
                .objects
                .filter(problem_in_contest__contest=contest, user=self.request.user)
                .select_related('problem_in_contest', 'compiler')
                .order_by('-created_at')
            )
        return attempts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contest = Contest.objects.get(id=self.kwargs['contest_id'])
        context.update(contest=contest)
        return context


class SourceView(TemplateView):
    template_name = 'contests/source.html'

    def get_context_data(self, *, attempt_id, **kwargs):
        context = super().get_context_data(id=attempt_id, **kwargs)
        contest = None
        attempt = None
        if self.request.user.is_authenticated():
            attempt = Attempt.objects.get(id=attempt_id)
            if attempt is not None:
                contest = attempt.problem_in_contest.contest
        context.update(contest=contest, attempt=attempt)
        return context


class ErrorsView(TemplateView):
    template_name = 'contests/errors.html'

    def get_context_data(self, *, attempt_id, **kwargs):
        context = super().get_context_data(id=attempt_id, **kwargs)
        contest = None
        attempt = None
        if self.request.user.is_authenticated():
            attempt = Attempt.objects.get(id=attempt_id)
            if attempt is not None:
                contest = attempt.problem_in_contest.contest
        context.update(contest=contest, attempt=attempt)
        return context
