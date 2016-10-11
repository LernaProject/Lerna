from django.conf.urls import url

from .views import RatingIndexView

urlpatterns = (
    url(r'^rating$', RatingIndexView.as_view(), name='rating'),
    url(r'^rating/(?P<page>\d+)/$', RatingIndexView.as_view(), name='rating'),
)
