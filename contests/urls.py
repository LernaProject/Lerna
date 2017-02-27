from django.conf.urls import url

from .views import (
    ContestIndexView, TrainingIndexView, TrainingView, ProblemView, AttemptsView, SourceView,
    ErrorsView, SubmitView, RatingView, StandingsView
)

urlpatterns = (
    url(r'^$', ContestIndexView.as_view(), name='contests'),
    url(r'^trainings/?$', TrainingIndexView.as_view(), name='trainings'),
    url(r'^training/(?P<contest_id>\d+)/?$', TrainingView.as_view(), name='training'),
    url(r'^training/(?P<contest_id>\d+)/(?P<problem_number>\d+)/?$', ProblemView.as_view(), name='problem'),
    url(r'^submit/(?P<contest_id>\d+)/?$', SubmitView.as_view(), name='submit'),
    url(r'^attempts/(?P<contest_id>\d+)/?$', AttemptsView.as_view(), name='attempts'),
    url(r'^attempts/(?P<contest_id>\d+)/(?P<page>\d+)/?$', AttemptsView.as_view(), name='attempts'),
    url(r'^source/(?P<attempt_id>\d+)/?$', SourceView.as_view(), name='source'),
    url(r'^errors/(?P<attempt_id>\d+)/?$', ErrorsView.as_view(), name='errors'),
    url(r'^rating/(?P<contest_id>\d+)/?$', RatingView.as_view(), name='rating'),
    url(r'^rating/(?P<contest_id>\d+)/(?P<page>\d+)/?$', RatingView.as_view(), name='rating'),
    url(r'^standings/(?P<contest_id>\d+)/?$', StandingsView.as_view(), name='standings'),
)
