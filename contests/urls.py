from django.conf.urls import url

from redirector import redirect_to
from .views     import ContestIndexView
from .views     import TrainingIndexView
from .views     import TrainingView

urlpatterns = (
    url(R"^$", ContestIndexView.as_view(), name="index"),
    url(R"^trainings$", TrainingIndexView.as_view(), name="trainings"),
    url(R"^training/(?P<id>\d+)$", TrainingView.as_view(), name="training"),
)
