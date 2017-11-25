from django.conf.urls import url

from .views import AchievementsView

urlpatterns = (
    url(r'^(?P<user_id>\d+)?$', AchievementsView.as_view(), name='achievements'),
)
