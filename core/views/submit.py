from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts           import render, redirect
from django.views.generic       import View

from .util       import NotificationListMixin, SelectContestMixin, get_relative_time_info
from core.forms  import SubmitForm
from core.models import ProblemInContest, Compiler


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
