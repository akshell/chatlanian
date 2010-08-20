# (c) 2010 by Anton Korenyushkin

from django.conf.urls.defaults import *

from resource import Resource
from app_handlers import (
    AppHandler, EnvsHandler, EnvHandler, DomainsHandler,
    CodeHandler, FileHandler)


urlpatterns = patterns(
    '',
    (r'^$', Resource(AppHandler)),
    (r'^envs/$', Resource(EnvsHandler)),
    (r'^envs/(?P<env_name>[a-zA-Z0-9-]+)$', Resource(EnvHandler)),
    (r'^domains$', Resource(DomainsHandler)),
    (r'^code/$', Resource(CodeHandler)),
    (r'^code/(?P<path>.+)$', Resource(FileHandler)),
)
