from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from core.models import Problem, Contest, ProblemInContest, Attempt

import datetime
import pytz

import os

class ContestIndexView(TemplateView):
    template_name = 'contests/contests.html'

    def get_context_data(self, **kwargs):
        def get_contests():
            time_now = datetime.datetime.now(pytz.timezone('US/Pacific')) # TODO: not US/Pacific! Use local settings 
            contests = Contest.objects.filter(is_training=False)
            actual = []
            wait = []
            past = []
            for contest in contests:
                if time_now < contest.start_time:
                    wait.append(contest)
                elif contest.start_time + datetime.timedelta(minutes=contest.duration) < time_now:
                    past.append(contest)
                else:
                    actual.append(contest)
            return actual, wait, past

        context = super().get_context_data(**kwargs)
        context['actual_contest_list'], context['wait_contest_list'], context['past_contest_list'] = get_contests()
        return context


class TrainingIndexView(TemplateView):
    template_name = 'contests/trainings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trainings_raw = (
            Contest.objects.filter(is_training=True)
            .order_by("name")
        )

        trainings = []
        cur_prefixes = []

        for t in trainings_raw:
            name_parts = t.name.split('/')

            cur_prefixes = os.path.commonprefix([name_parts, cur_prefixes])
            idx = len(cur_prefixes)

            while idx < len(name_parts):
                if idx == len(name_parts) - 1:
                    trainings.append({'tab': ' '*idx, 'is_terminal': True, 'id': t.id, 'name': name_parts[idx]})
                else:
                    cur_prefixes.append(name_parts[idx])
                    trainings.append({'tab': ' '*idx, 'is_terminal': False, 'id': None, 'name': name_parts[idx]})
                idx += 1

        context.update(trainings=trainings)
        return context


class TrainingView(TemplateView):
    template_name = 'contests/training.html'

    def get_context_data(self, *, id, **kwargs):
        context = super().get_context_data(id=id, **kwargs)
        training = Contest.objects.get(id=id)
        pics = (
            ProblemInContest.objects
            .filter(contest=training)
            .order_by("number")
            .select_related("problem")
        )
        context.update(contest=training, pics=pics)
        return context

class AttemptsView(TemplateView):
    template_name = 'contests/attempts.html'

    def get_context_data(self, *, id, **kwargs):
        context = super().get_context_data(id=id, **kwargs)
        training = Contest.objects.get(id=id)
        if self.request.user.is_authenticated():
          attempts = (
              Attempt.objects
                  .filter(problem_in_contest__contest=training)
                  .filter(user_id=self.request.user.id)
                  .order_by("-time")
                  .select_related("problem_in_contest")
                  .select_related("compiler")
          )
        else:
          attempts = None
        context.update(contest=training, attempts=attempts)
        return context
