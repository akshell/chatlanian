# (c) 2010 by Anton Korenyushkin

import os
import httplib

from piston.handler import BaseHandler
from piston.utils import require_mime
from django.http import HttpResponse

from paths import devs_path, create_app
from utils import read_file, write_file, check_name


class ConfigHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')

    def read(self, request):
        return HttpResponse(
            read_file(devs_path[request.dev_name].config),
            'application/json; charset=utf-8')

    @require_mime('json')
    def update(self, request):
        write_file(devs_path[request.dev_name].config, request.raw_post_data)
        return HttpResponse()


class RsaPubHandler(BaseHandler):
    allowed_methods = ('GET')
    handles_anonyms = False

    def read(self, request):
        return HttpResponse(
            read_file(devs_path[request.dev_name].rsa_pub),
            'text/plain; charset=utf-8')


class AppsHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')

    def read(self, request):
        apps_path = devs_path[request.dev_name].apps
        lower_names = os.listdir(apps_path)
        lower_names.sort()
        return [
            read_file(apps_path[lower_name].name)
            for lower_name in lower_names
        ]

    def create(self, request):
        name = request.data['name']
        check_name(name)
        create_app(request.dev_name, name)
        return HttpResponse(status=httplib.CREATED)
