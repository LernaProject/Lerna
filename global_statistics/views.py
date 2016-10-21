from django.views.generic import ListView
from django.db.models import Count, Case, When, Q, F

from users.models import User
from core.models import Attempt

class RatingIndexView(ListView):
    template_name = 'global_statistics/rating.html'
    context_object_name = 'user_list'
    queryset = (
        User
        .objects
        .all()
        .annotate(
            rating=Count(
                Case(
                    When(attempt__problem_in_contest__contest__is_admin=True, then=None),
                    When(
                        attempt__result='Accepted',
                        then=F('attempt__problem_in_contest__problem_id')
                    ),
                    When(
                        Q(attempt__result='Tested', attempt__score='100'),
                        then=F('attempt__problem_in_contest__problem_id')
                    ),
                    default=None,
                ),
                distinct=True,
            )
        )
        .exclude(rating=0)
    )
    ordering = '-rating'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1


class AttemptsView(ListView):
    template_name = 'global_statistics/attempts.html'
    context_object_name = 'attempts'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
        attempts = None
        if self.request.user.is_authenticated():
            attempts = (
                Attempt
                .objects
                .filter(user=self.request.user)
                .select_related('problem_in_contest', 'compiler')
                .order_by('-created_at')
            )
        return attempts
