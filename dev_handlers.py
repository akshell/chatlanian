# (c) 2010 by Anton Korenyushkin

from __future__ import with_statement

from piston.handler import BaseHandler
from piston.utils import require_mime
from django.http import HttpResponse

from paths import get_dev_path, get_config_path


class ConfigHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')

    def read(self, request):
        with open(get_config_path(request.user.username)) as f:
            return HttpResponse(f.read(), 'application/json')

    @require_mime('json')
    def update(self, request):
        with open(get_config_path(request.user.username), 'w') as f:
            f.write(request.raw_post_data)
        return HttpResponse()


class RsaPubHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):
        with open(get_dev_path(request.user.username) + '/rsa.pub') as f:
            return HttpResponse(f.read(), 'text/plain')
