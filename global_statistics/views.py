from django.views.generic import ListView
from django.db.models import Count, F, Q, Min
from users.models import User, rank_users
from core.models import Attempt, Problem, Contest


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
                Q(attempt__result='Accepted') | Q(attempt__result='Tested', attempt__score__gt=99.99)
            )
            .annotate(problems_solved=Count('attempt__problem_in_contest__problem', distinct=True))
            .order_by('-problems_solved')
        )
        rank_users(users, 'problems_solved')
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
        user = None
        if self.request.user.is_authenticated():
            user = self.request.user
        attempts = (
            Attempt
            .objects
            .filter(user=user)
            .select_related('problem_in_contest', 'compiler')
            .order_by('-created_at')
        )
        return attempts


class BestTimeView(ListView):
    template_name = 'global_statistics/best_time.html'
    context_object_name = 'user_list'
    allow_empty = True
    paginate_by = 25
    paginate_orphans = 1

    def get_queryset(self):
        problem = Problem.objects.get(id=self.kwargs['problem_id'])
        users = (
            User
            .objects
            .filter(
                Q(attempt__problem_in_contest__contest__is_admin=False),
                Q(attempt__problem_in_contest__problem_id=problem.id),
                Q(attempt__result='Accepted') | Q(attempt__result='Tested', attempt__score__gt=99.99)
            )
            .annotate(best_time=Min('attempt__used_time'))
            .annotate(compiler=Min('attempt__compiler__name'))
            .order_by('best_time')
        )
        rank_users(users, 'best_time')
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        problem = Problem.objects.get(id=self.kwargs['problem_id'])
        context.update(problem=problem)
        return context


class ProblemInTrainingsView(ListView):
    template_name = 'global_statistics/problem_in_trainings.html'
    context_object_name = 'training_list'

    def get_queryset(self):
        problem = Problem.objects.get(id=self.kwargs['problem_id'])
        trainings = (
            Contest
            .objects
            .filter(
                problem_in_contest_set__problem_id=problem.id,
                is_training=True,
                is_admin=False,
            )
            .only('id', 'name')
            .annotate(problem_number=F('problem_in_contest_set__number'))
            .order_by('name')
        )
        return trainings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        problem = Problem.objects.get(id=self.kwargs['problem_id'])
        context.update(problem=problem)
        return context
