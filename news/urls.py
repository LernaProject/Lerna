from django.conf.urls import url

from redirector import redirect_to
from .views     import IndexView, DetailView

urlpatterns = (
    url(R"^$", IndexView.as_view(), name="index"),
    url(R"^(?P<page>\d+)/$", IndexView.as_view(), name="index"),
    url(R"^show/(?P<pk>\d+)/$", DetailView.as_view(), name="show"),

    # For compatibility only.
    url(R"^list_news/(?P<page>\d+)/$", redirect_to("news:index")),
)
