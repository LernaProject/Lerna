from django.conf.urls import url

from . import views

urlpatterns = (
    url(R"^$", views.IndexView.as_view(), name="index"),
    url(R"^(?P<page>\d+)/$", views.IndexView.as_view(), name="index"),
    url(R"^show/(?P<pk>\d+)/$", views.DetailView.as_view(), name="show"),

    # For compatibility only.
    # TODO: Replace with redirection pages.
    url(R"^list_news/(?P<page>\d+)/$", views.IndexView.as_view()),
)
