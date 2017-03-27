from django.views.generic import TemplateView

from .util       import NotificationListMixin, SelectContestMixin, get_relative_time_info
from core.models import ProblemInContest


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
