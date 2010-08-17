# (c) 2010 by Anton Korenyushkin

from django.conf.urls.defaults import *
from django.contrib import admin

from resource import Resource
from auth_handlers import SignupHandler, LoginHandler, LogoutHandler
from dev_handlers import ConfigHandler


admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^signup$', Resource(SignupHandler)),
    (r'^login$', Resource(LoginHandler)),
    (r'^logout$', Resource(LogoutHandler)),
    (r'^config$', Resource(ConfigHandler)),
)
