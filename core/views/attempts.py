from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions     import PermissionDenied
from django.http                import Http404
from django.views.generic       import TemplateView, ListView

from .util       import NotificationListMixin, SelectContestMixin, get_relative_time_info
from core.models import Attempt
from core.util   import highlight_source


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

        source, styles = highlight_source(attempt.source, attempt.compiler.highlighter)
        context.update(
            contest=attempt.problem_in_contest.contest,
            attempt=attempt,
            notifications=self.get_notifications(attempt.problem_in_contest.contest),
            highlighted_source=source,
            highlighting_styles=styles,
        )
        return context
