from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit  import FormView

from .util       import NotificationListMixin, SelectContestMixin, get_relative_time_info
from core.forms  import ClarificationForm
from core.models import Clarification
from core.util   import notify_admins_about_clarification


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
            notify_admins_about_clarification(self.request, form.ask(self.request.user, contest))

        return super().form_valid(form)

    def get_success_url(self):
        return self.request.get_full_path()
