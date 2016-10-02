from django.conf.urls import url

from .views import ContestIndexView, TrainingIndexView, TrainingView, AttemptsView, SourceView, ErrorsView

urlpatterns = (
    url(R"^$", ContestIndexView.as_view(), name="index"),
    url(R"^trainings$", TrainingIndexView.as_view(), name="trainings"),
    url(R"^training/(?P<id>\d+)$", TrainingView.as_view(), name="training"),
    url(R"^attempts/(?P<id>\d+)$", AttemptsView.as_view(), name="attempts"),
    url(R"^source/(?P<id>\d+)$", SourceView.as_view(), name="source"),
    url(R"^errors/(?P<id>\d+)$", ErrorsView.as_view(), name="errors"),
)
