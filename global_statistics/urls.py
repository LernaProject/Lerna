from django.conf.urls import url

from .views import RatingIndexView

urlpatterns = (
    url(R"^rating$", RatingIndexView.as_view(), name="rating"),
    url(R"^rating/(?P<page>\d+)/$", RatingIndexView.as_view(), name="rating"),
)
