from django.conf.urls import url

from .views import RatingIndexView, AttemptsView, BestTimeView, ProblemInTrainingsView

urlpatterns = (
    url(r'^rating$', RatingIndexView.as_view(), name='rating'),
    url(r'^rating/(?P<page>\d+)$', RatingIndexView.as_view(), name='rating'),
    url(r'^attempts$', AttemptsView.as_view(), name='attempts'),
    url(r'^attempts/(?P<page>\d+)$', AttemptsView.as_view(), name='attempts'),
    url(r'^best_time/(?P<problem_id>\d+)$', BestTimeView.as_view(), name='best_time'),
    url(r'^best_time/(?P<problem_id>\d+)/(?P<page>\d+)$', BestTimeView.as_view(), name='best_time'),
    url(r'^problem_in_trainings/(?P<problem_id>\d+)$', ProblemInTrainingsView.as_view(), name='problem_in_trainings'),
)
