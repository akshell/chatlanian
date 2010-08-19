# (c) 2010 by Anton Korenyushkin

from piston.handler import BaseHandler
from piston.utils import require_mime
from django.http import HttpResponse

from paths import get_dev_path, get_config_path
from utils import read_file, write_file


class ConfigHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')

    def read(self, request):
        return HttpResponse(
            read_file(get_config_path(request.dev_name)),
            'application/json; charset=utf-8')

    @require_mime('json')
    def update(self, request):
        write_file(get_config_path(request.dev_name), request.raw_post_data)
        return HttpResponse()


class RsaPubHandler(BaseHandler):
    allowed_methods = ('GET')
    handles_anonyms = False

    def read(self, request):
        return HttpResponse(
            read_file(get_dev_path(request.dev_name) + '/rsa.pub'),
            'text/plain; charset=utf-8')
