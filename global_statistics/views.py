from django.views.generic import ListView
from django.db.models import Count, Q

from users.models import User
from core.models import Attempt, Problem

class RatingIndexView(ListView):
    template_name = 'global_statistics/rating.html'
    context_object_name = 'user_list'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
        users = (
            User
            .objects
            .filter(
                Q(attempt__problem_in_contest__contest__is_admin=False),
                Q(attempt__result='Accepted') | Q(attempt__result='Tested', attempt__score__gt=99.99),
            )
            .annotate(problems_solved=Count('attempt__problem_in_contest__problem', distinct=True))
            .order_by('-problems_solved')
        )

        if len(users) > 0:
            rank_top = 0
            rank_bottom = 0
            for i in range(1, len(users) + 1):
                rank_bottom += 1
                if i == len(users) or users[i].problems_solved != users[i-1].problems_solved:
                    if rank_top == rank_bottom - 1:
                        users[rank_top].rank = '{0}'.format(rank_top + 1)
                    else:
                        for rank in range(rank_top, rank_bottom):
                            users[rank].rank = '{0}-{1}'.format(rank_top + 1, rank_bottom)
                    rank_top = rank_bottom

        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        problems_total_amount = Problem.objects.all().count
        context.update(problems_total_amount=problems_total_amount)
        return context


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
