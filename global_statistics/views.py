from django.contrib.auth.mixins   import LoginRequiredMixin
from django.db.models             import F, Q, Count
from django.db.models.expressions import RawSQL
from django.http                  import Http404
from django.utils                 import timezone
from django.views.generic         import ListView

from core.models  import Attempt, Problem, Contest, ProblemInContest
from users.models import User, rank_users


def _to_minutes(expression):
    return expression * RawSQL("interval '1 minute'", ())


class RatingIndexView(ListView):
    template_name = 'global_statistics/rating.html'
    context_object_name = 'user_list'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
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
                        JOIN contests c ON c.id = pic.contest_id
                        WHERE NOT c.is_admin
                        AND (c.is_training OR (
                            c.is_unfrozen AND
                            now() >= c.start_time + c.duration * interval '1 minute'
                        ))
                        AND (a.result = 'Accepted' OR (a.result = 'Tested' AND a.score > 99.99))
                        GROUP BY u.id, pic.problem_id
                    ) subq
                    GROUP BY id
                ) subq
                JOIN users u ON u.id = subq.id
                WHERE subq.problems_solved >= 10
                ORDER BY subq.problems_solved DESC, subq.last_success
            """)
        )
        rank_users(users, 'problems_solved')
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        problems_total_amount = (
            ProblemInContest
            .objects
            .filter(contest__is_admin=False)
            .aggregate(c=Count('problem', distinct=True))
        )['c']

        context.update(problems_total_amount=problems_total_amount)
        return context


class AttemptsView(LoginRequiredMixin, ListView):
    template_name = 'global_statistics/attempts.html'
    context_object_name = 'attempts'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    get_queryset = lambda self: (
        Attempt
        .objects
        .filter(user=self.request.user)
        .select_related('problem_in_contest__problem', 'problem_in_contest__contest', 'compiler')
        .only(
            'created_at', 'compiler__name', 'result', 'score', 'used_time', 'used_memory',
            'problem_in_contest__number',
            'problem_in_contest__problem__name', 'problem_in_contest__contest__name',
        )
        .order_by('-created_at')
    )


class BestTimeView(ListView):
    template_name = 'global_statistics/best_time.html'
    context_object_name = 'user_list'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
        now = timezone.now()
        users = list(
            User
            .objects
            .filter(
                Q(attempt__problem_in_contest__contest__is_training=True) | Q(
                    attempt__problem_in_contest__contest__is_unfrozen=True,
                    # start_time <= now() - duration * interval '1 minute'
                    attempt__problem_in_contest__contest__start_time__lte=(
                        now - _to_minutes(F('attempt__problem_in_contest__contest__duration'))
                    ),
                ),
                Q(attempt__result='Accepted') | Q(
                    attempt__result='Tested',
                    attempt__score__gt=99.99,
                ),
                attempt__problem_in_contest__contest__is_admin=False,
                attempt__problem_in_contest__problem=self.kwargs['problem_id'],
            )
            .annotate(
                best_time=F('attempt__used_time'),
                best_memory=F('attempt__used_memory'),
                compiler=F('attempt__compiler__name'),
                submitted_at=F('attempt__created_at'),
            )
            .only('username')
            .order_by('id', 'attempt__used_time', 'attempt__used_memory', 'attempt')
            .distinct('id')
        )
        users.sort(key=lambda u: (u.best_time, u.best_memory, u.submitted_at))
        rank_users(users, 'best_time')
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empty = not context['user_list']
        if empty and not ProblemInContest.objects.is_visible(self.kwargs['problem_id']):
            raise Http404
        problem = Problem.objects.only('name').get(id=self.kwargs['problem_id'])
        context.update(problem=problem)
        return context


class ProblemInTrainingsView(ListView):
    template_name = 'global_statistics/problem_in_trainings.html'
    context_object_name = 'training_list'
    allow_empty = True

    get_queryset = lambda self: (
        Contest
        .objects
        .filter(
            problem_in_contest_set__problem=self.kwargs['problem_id'],
            is_training=True,
            is_admin=False,
        )
        .only('id', 'name', 'is_training')
        .annotate(problem_number=F('problem_in_contest_set__number'))
        .order_by('name')
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empty = not context['training_list']
        if empty and not ProblemInContest.objects.is_visible(self.kwargs['problem_id']):
            raise Http404
        problem = Problem.objects.only('name').get(id=self.kwargs['problem_id'])
        context.update(problem=problem)
        return context
