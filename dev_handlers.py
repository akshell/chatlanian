# (c) 2010 by Anton Korenyushkin

from httplib import CREATED
import os

import simplejson as json
from piston.handler import BaseHandler
from piston.utils import require_mime
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.mail import send_mail

from settings import DEBUG, ADMINS
from utils import read_file, write_file, check_name
from paths import SAMPLE_NAME, ROOT
from managers import create_app
from resource import HALF_ANONYMOUS


def _get_apps(dev_name):
    apps_path = ROOT.devs[dev_name].apps
    return [
        read_file(apps_path[lower_name].name)
        for lower_name in sorted(os.listdir(apps_path))
    ]


class IndexHandler(BaseHandler):
    allowed_methods = ('GET',)

    def get(self, request):
        if request.is_anonymous:
            apps = [SAMPLE_NAME]
            config = '{}'
        else:
            apps = _get_apps(request.dev_name)
            config = read_file(ROOT.devs[request.dev_name].config)
        return render_to_response(
            'index.html',
            {
                'DEBUG': DEBUG,
                'username': request.user.username,
                'apps': json.dumps(apps),
                'config': config,
            })


class ConfigHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')

    def get(self, request):
        return HttpResponse(
            read_file(ROOT.devs[request.dev_name].config),
            'application/json; charset=utf-8')

    @require_mime('json')
    def put(self, request):
        write_file(ROOT.devs[request.dev_name].config, request.raw_post_data)
        return HttpResponse()


class RsaPubHandler(BaseHandler):
    allowed_methods = ('GET')
    access = HALF_ANONYMOUS

    def get(self, request):
        return HttpResponse(
            read_file(ROOT.devs[request.dev_name].rsa_pub),
            'text/plain; charset=utf-8')


class ContactHandler(BaseHandler):
    allowed_methods = ('POST',)

    def post(self, request):
        send_mail(
            'Contact',
            request.data['message'],
            request.data['email'].strip(),
            (ADMINS[0][1],))
        return HttpResponse()


class AppsHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')

    def get(self, request):
        return _get_apps(request.dev_name)

    def post(self, request):
        app_name = request.data['name']
        check_name(app_name)
        create_app(request.dev_name, app_name)
        return HttpResponse(status=CREATED)
