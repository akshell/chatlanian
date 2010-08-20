# (c) 2010 by Anton Korenyushkin

from django.conf.urls.defaults import *

from resource import Resource
from app_handlers import AppHandler


urlpatterns = patterns(
    '',
    (r'^$', Resource(AppHandler)),
)
