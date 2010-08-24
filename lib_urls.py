# (c) 2010 by Anton Korenyushkin

from django.conf.urls.defaults import *

from resource import Resource
from lib_handlers import OwnerHandler, LibHandler, VersionHandler, BlobHandler


version_urlpatterns = patterns(
    '',
    (r'^$', Resource(VersionHandler)),
    (r'^(?P<path>.*)$', Resource(BlobHandler)),
)

lib_urlpatterns = patterns(
    '',
    (r'^$', Resource(LibHandler)),
    (r'^(?P<version>[^/]+)/', include(version_urlpatterns)),
)

urlpatterns = patterns(
    '',
    (r'^$', Resource(OwnerHandler)),
    (r'^(?P<lib_name>[a-zA-Z0-9-]+)/', include(lib_urlpatterns)),
)
