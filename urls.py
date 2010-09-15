# (c) 2010 by Anton Korenyushkin

from django.conf.urls.defaults import *
from django.contrib import admin

from utils import NAME_PATTERN
from resource import Resource
from auth_handlers import SignupHandler, LoginHandler, LogoutHandler
from dev_handlers import IndexHandler, ConfigHandler, RsaPubHandler, AppsHandler


admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^$', Resource(IndexHandler)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^signup$', Resource(SignupHandler)),
    (r'^login$', Resource(LoginHandler)),
    (r'^logout$', Resource(LogoutHandler)),
    (r'^config$', Resource(ConfigHandler)),
    (r'^rsa\.pub$', Resource(RsaPubHandler)),
    (r'^apps/$', Resource(AppsHandler)),
    (r'^apps/(?P<app_name>%s)/' % NAME_PATTERN, include('chatlanian.app_urls')),
    (r'^libs/(?P<owner_name>%s)/' % NAME_PATTERN,
     include('chatlanian.lib_urls')),
)
