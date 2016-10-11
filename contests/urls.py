from django.conf.urls import url

from .views import (
    ContestIndexView, TrainingIndexView, TrainingView, AttemptsView, SourceView, ErrorsView,
    SubmitView,
)

urlpatterns = (
    url(r'^$', ContestIndexView.as_view(), name='contests'),
    url(r'^trainings$', TrainingIndexView.as_view(), name='trainings'),
    url(r'^training/(?P<contest_id>\d+)$', TrainingView.as_view(), name='training'),
    url(r'^submit/(?P<contest_id>\d+)$', SubmitView.as_view(), name='submit'),
    url(r'^attempts/(?P<contest_id>\d+)$', AttemptsView.as_view(), name='attempts'),
    url(r'^source/(?P<attempt_id>\d+)$', SourceView.as_view(), name='source'),
    url(r'^errors/(?P<attempt_id>\d+)$', ErrorsView.as_view(), name='errors'),
)
