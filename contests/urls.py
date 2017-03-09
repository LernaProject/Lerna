from django.conf.urls import url

from .views import (
    ContestIndexView, TrainingIndexView, TrainingView, ProblemView, AttemptsView,
    AttemptDetailsView, SubmitView, RatingView, StandingsView, UnfrozenStandingsView,
    ClarificationsView,
)


def _url(regex, cls, name):
    return url(regex, cls.as_view(), name=name)


urlpatterns = (
    _url(r'^$', ContestIndexView, 'contests'),
    _url(r'^trainings/?$', TrainingIndexView, 'trainings'),
    _url(r'^training/(?P<contest_id>\d+)/?$', TrainingView, 'training'),
    _url(r'^problem/(?P<contest_id>\d+)/(?P<problem_number>\d+)/?$', ProblemView, 'problem'),
    _url(r'^submit/(?P<contest_id>\d+)/?$', SubmitView, 'submit'),
    _url(r'^attempts/(?P<contest_id>\d+)/?$', AttemptsView, 'attempts'),
    _url(r'^attempts/(?P<contest_id>\d+)/(?P<page>\d+)/?$', AttemptsView, 'attempts'),
    _url(r'^attempt/(?P<attempt_id>\d+)/?$', AttemptDetailsView, 'attempt'),
    _url(r'^rating/(?P<contest_id>\d+)/?$', RatingView, 'rating'),
    _url(r'^rating/(?P<contest_id>\d+)/(?P<page>\d+)/?$', RatingView, 'rating'),
    _url(r'^standings/(?P<contest_id>\d+)/?$', StandingsView, 'standings'),
    _url(r'^unfrozen_standings/(?P<contest_id>\d+)/?$', UnfrozenStandingsView, 'unfrozen_standings'),
    _url(r'^clarifications/(?P<contest_id>\d+)/?$', ClarificationsView, 'clarifications'),
)
