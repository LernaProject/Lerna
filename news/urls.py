from django.conf.urls import url

from redirector import redirect_to
from .views     import IndexView, DetailView

urlpatterns = (
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<page>\d+)/$', IndexView.as_view(), name='index'),
    url(r'^show/(?P<pk>\d+)/$', DetailView.as_view(), name='show'),

    # For compatibility only.
    url(r'^list_news/(?P<page>\d+)/$', redirect_to('news:index')),
)
