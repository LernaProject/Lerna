from django.conf.urls import url

from .views import RatingIndexView, AttemptsView

urlpatterns = (
    url(r'^rating$', RatingIndexView.as_view(), name='rating'),
    url(r'^rating/(?P<page>\d+)$', RatingIndexView.as_view(), name='rating'),
    url(r'^attempts$', AttemptsView.as_view(), name='attempts'),
    url(r'^attempts/(?P<page>\d+)$', AttemptsView.as_view(), name='attempts'),
)
