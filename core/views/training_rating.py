from django.db.models.expressions import RawSQL
from django.views.generic         import ListView

from .util        import NotificationListMixin, SelectContestMixin
from core.models  import Attempt, ProblemInContest
from users.models import User, rank_users


class RatingView(SelectContestMixin, NotificationListMixin, ListView):
    template_name = 'contests/trainings/rating.html'
    context_object_name = 'user_list'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
        contest_id = self.kwargs['contest_id']
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
                        WHERE pic.contest_id = %s
                        AND (a.result = 'Accepted' OR (a.result = 'Tested' AND a.score > 99.99))
                        GROUP BY u.id, a.problem_in_contest_id
                    ) subq
                    GROUP BY id
                ) subq
                JOIN users u ON u.id = subq.id
                ORDER BY subq.problems_solved DESC, subq.last_success
            """, [contest_id])
        )
        rank_users(users, 'problems_solved')
        pattern = ['.'] * ProblemInContest.objects.filter(contest=contest_id).count()
        statuses = {}
        for user in users:
            statuses[user.id] = user.problems_status = pattern[:]

        tried = (
            Attempt
            .objects
            .filter(problem_in_contest__contest=contest_id)
            .exclude(result__in=['', 'Queued', 'Compiling...', 'Compilation error', 'Ignored'])
            .exclude(result__startswith='Testing')
            .exclude(result__startswith='System error')
            .annotate(succeeded=RawSQL(
                "result = 'Accepted' OR (result = 'Tested' AND attempts.score > 99.99)",
                (),
            ))
            .distinct()
            .values_list('user', 'problem_in_contest__number', 'succeeded')
        )
        for user_id, number, succeeded in tried:
            try:
                status = statuses[user_id]
            except KeyError:
                pass  # Skip users that don't have at least 1 accepted problem.
            else:
                if succeeded:
                    status[number - 1] = '+'
                elif status[number - 1] != '+':
                    status[number - 1] = '-'

        return users

    def get_context_data(self, **kwargs):
        training = self.select_contest()
        problems = (
            ProblemInContest
            .objects
            .filter(contest=training)
            .select_related('problem', 'contest')
            .only('number', 'problem__name', 'contest__is_training')
            .order_by('number')
        )

        context = super().get_context_data(**kwargs)
        context.update(
            contest=training,
            problems=problems,
            notifications=self.get_notifications(training),
        )
        return context
