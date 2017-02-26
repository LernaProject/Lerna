"""
lerna URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from ajax_select         import urls as ajax_select_urls
from django.conf         import settings
from django.conf.urls    import include, url
from django.contrib      import admin

from news.views  import IndexView
from users.views import Registration, Login, Logout

urlpatterns = (
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^news/', include('news.urls', namespace='news')),
    url(r'^contests/', include('contests.urls', namespace='contests')),
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
