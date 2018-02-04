from django.conf.urls import url

from .views import RatingIndexView, AttemptsView, BestTimeView, ProblemInTrainingsView, UserProblemsView, \
    UserProblemsByTimeView

urlpatterns = (
    url(r'^rating/?$', RatingIndexView.as_view(), name='rating'),
    url(r'^rating/(?P<page>\d+)/?$', RatingIndexView.as_view(), name='rating'),
    url(r'^attempts/?$', AttemptsView.as_view(), name='attempts'),
    url(r'^attempts/(?P<page>\d+)/?$', AttemptsView.as_view(), name='attempts'),
    url(r'^(?P<problem_id>\d+)/best_time/?$', BestTimeView.as_view(), name='best_time'),
    url(r'^(?P<problem_id>\d+)/best_time/(?P<page>\d+)/?$', BestTimeView.as_view(), name='best_time'),
    url(r'^(?P<problem_id>\d+)/problem_in_trainings/?$', ProblemInTrainingsView.as_view(), name='problem_in_trainings'),
    url(r'^user_problems/(?P<user_id>\d+)/?$', UserProblemsView.as_view(), name='user_problems'),
    url(r'^user_problems/(?P<user_id>\d+)/(?P<page>\d+)/?$', UserProblemsView.as_view(), name='user_problems'),
    url(r'^user_problems/(?P<user_id>\d+)/sort_by_time/?$', UserProblemsByTimeView.as_view(),
        name='user_problems_sorted_by_time'),
    url(r'^user_problems/(?P<user_id>\d+)/(?P<page>\d+)/sort_by_time/?$', UserProblemsByTimeView.as_view(),
        name='user_problems_sorted_by_time'),
)
