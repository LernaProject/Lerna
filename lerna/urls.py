from ajax_select      import urls as ajax_select_urls
from django.conf      import settings
from django.conf.urls import include, url
from django.contrib   import admin

from news.views  import IndexView
from users.views import Registration, Login, Logout

urlpatterns = (
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^news/', include('news.urls', namespace='news')),
    url(r'^contests/', include('core.urls', namespace='contests')),
    url(r'^global_statistics/', include('global_statistics.urls', namespace='global_statistics')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ajax_select/', include(ajax_select_urls)),

    url(r'^login/?$', Login.as_view(), name='login'),
    url(r'^logout/?$', Logout.as_view(), name='logout'),
    url(r'^registration/?$', Registration.as_view(), name='registration'),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += (
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
