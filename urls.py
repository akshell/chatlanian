# (c) 2010 by Anton Korenyushkin

from django.conf.urls.defaults import *
from django.contrib import admin

from resource import Resource
from auth_handlers import SignupHandler, LoginHandler, LogoutHandler
from dev_handlers import ConfigHandler, RsaPubHandler, AppsHandler


admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^signup$', Resource(SignupHandler)),
    (r'^login$', Resource(LoginHandler)),
    (r'^logout$', Resource(LogoutHandler)),
    (r'^config$', Resource(ConfigHandler)),
    (r'^rsa\.pub$', Resource(RsaPubHandler)),
    (r'^apps/$', Resource(AppsHandler)),
    (r'^apps/(?P<app_name>[a-zA-Z0-9-]+)/', include('chatlanian.app_urls')),
    (r'^libs/(?P<owner_name>[a-zA-Z0-9-]+)/', include('chatlanian.lib_urls')),
)
