# (c) 2010 by Anton Korenyushkin

from django.conf.urls.defaults import *
from django.contrib import admin

from utils import make_resource
from auth_handlers import SignupHandler, LoginHandler, LogoutHandler


admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^signup$', make_resource(SignupHandler)),
    (r'^login$', make_resource(LoginHandler)),
    (r'^logout$', make_resource(LogoutHandler)),
)
