# (c) 2010 by Anton Korenyushkin

from django.conf.urls.defaults import *
from django.contrib import admin

from utils import NAME_PATTERN
from resource import Resource
from auth_handlers import (
    SignupHandler, LoginHandler, LogoutHandler, PasswordHandler,
    password_reset_view)
from dev_handlers import (
    IDEHandler, ConfigHandler, RsaPubHandler, ContactHandler, AppsHandler)


admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^ide/?$', Resource(IDEHandler)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^signup$', Resource(SignupHandler)),
    (r'^login$', Resource(LoginHandler)),
    (r'^logout$', Resource(LogoutHandler)),
    (r'^password$', Resource(PasswordHandler)),
    (r'^password/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)$', password_reset_view),
    (r'^config$', Resource(ConfigHandler)),
    (r'^rsa\.pub$', Resource(RsaPubHandler)),
    (r'^contact$', Resource(ContactHandler)),
    (r'^apps/$', Resource(AppsHandler)),
    (r'^apps/(?P<app_name>%s)/' % NAME_PATTERN, include('chatlanian.app_urls')),
    (r'^libs/(?P<owner_name>%s)/' % NAME_PATTERN,
     include('chatlanian.lib_urls')),
)
