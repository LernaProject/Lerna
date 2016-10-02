from django.conf.urls import url

from .views import ContestIndexView, TrainingIndexView, TrainingView, AttemptsView

urlpatterns = (
    url(R"^$", ContestIndexView.as_view(), name="index"),
    url(R"^trainings$", TrainingIndexView.as_view(), name="trainings"),
    url(R"^training/(?P<id>\d+)$", TrainingView.as_view(), name="training"),
    url(R"^attempts/(?P<id>\d+)$", AttemptsView.as_view(), name="attempts"),
)
