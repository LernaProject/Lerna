from django.conf.urls import url

from .views import IndexView, DetailView

urlpatterns = (
    url(R"^$", IndexView.as_view(), name="index"),
    url(R"^(?P<page>\d+)/$", IndexView.as_view(), name="index"),
    url(R"^show/(?P<pk>\d+)/$", DetailView.as_view(), name="show"),

    # For compatibility only.
    # TODO: Replace with redirection pages.
    url(R"^list_news/(?P<page>\d+)/$", IndexView.as_view()),
)
