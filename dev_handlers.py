# (c) 2010 by Anton Korenyushkin

from httplib import CREATED
import os

from piston.handler import BaseHandler
from piston.utils import require_mime
from django.http import HttpResponse

from utils import read_file, write_file, check_name
from paths import DEVS_PATH
from managers import create_app


class ConfigHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')

    def get(self, request):
        return HttpResponse(
            read_file(DEVS_PATH[request.dev_name].config),
            'application/json; charset=utf-8')

    @require_mime('json')
    def put(self, request):
        write_file(DEVS_PATH[request.dev_name].config, request.raw_post_data)
        return HttpResponse()


class RsaPubHandler(BaseHandler):
    allowed_methods = ('GET')
    handles_anonyms = False

    def get(self, request):
        return HttpResponse(
            read_file(DEVS_PATH[request.dev_name].rsa_pub),
            'text/plain; charset=utf-8')


class AppsHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')

    def get(self, request):
        apps_path = DEVS_PATH[request.dev_name].apps
        return [
            read_file(apps_path[lower_name].name)
            for lower_name in sorted(os.listdir(apps_path))
        ]

    def post(self, request):
        app_name = request.data['name']
        check_name(app_name)
        create_app(request.dev_name, app_name)
        return HttpResponse(status=CREATED)
