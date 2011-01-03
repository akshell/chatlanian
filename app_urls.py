# (c) 2010-2011 by Anton Korenyushkin

from django.conf.urls.defaults import *

from utils import NAME_PATTERN
from resource import Resource
from app_handlers import (
    AppHandler, EnvsHandler, EnvHandler, DomainsHandler, CodeHandler,
    FileHandler, GitHandler, DiffHandler, CommitHandler, PublicHandler)


urlpatterns = patterns(
    '',
    (r'^$', Resource(AppHandler)),
    (r'^envs/$', Resource(EnvsHandler)),
    (r'^envs/(?P<env_name>%s)$' % NAME_PATTERN, Resource(EnvHandler)),
    (r'^domains$', Resource(DomainsHandler)),
    (r'^code/$', Resource(CodeHandler)),
    (r'^code/(?P<path>.+)$', Resource(FileHandler)),
    (r'^git$', Resource(GitHandler)),
    (r'^diff$', Resource(DiffHandler)),
    (r'^commit$', Resource(CommitHandler)),
    (r'^public$', Resource(PublicHandler)),
)
