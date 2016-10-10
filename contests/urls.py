from django.conf.urls import url

from .views import ContestIndexView, TrainingIndexView, TrainingView, AttemptsView, SourceView, ErrorsView, SubmitView

urlpatterns = (
    url(R"^$", ContestIndexView.as_view(), name="contests"),
    url(R"^trainings$", TrainingIndexView.as_view(), name="trainings"),
    url(R"^training/(?P<contest_id>\d+)$", TrainingView.as_view(), name="training"),
    url(R"^submit/(?P<contest_id>\d+)$", SubmitView.as_view(), name="submit"),
    url(R"^attempts/(?P<contest_id>\d+)$", AttemptsView.as_view(), name="attempts"),
    url(R"^source/(?P<attempt_id>\d+)$", SourceView.as_view(), name="source"),
    url(R"^errors/(?P<attempt_id>\d+)$", ErrorsView.as_view(), name="errors"),
)
