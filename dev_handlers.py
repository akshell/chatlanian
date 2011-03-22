# (c) 2010-2011 by Anton Korenyushkin

from httplib import CREATED

import simplejson as json
from piston.handler import BaseHandler
from piston.utils import require_mime
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.mail import send_mail

from settings import DEBUG, ADMINS
from utils import read_file, write_file, check_name
from paths import SAMPLE_NAME, KAPPA_VERSION, ROOT
from managers import create_app, get_app_names, get_lib_names, read_config
from resource import HALF_ANONYMOUS


class IDEHandler(BaseHandler):
    allowed_methods = ('GET',)

    def get(self, request):
        if request.is_anonymous:
            app_names = [SAMPLE_NAME]
            lib_names = []
            config = {}
        else:
            app_names = get_app_names(request.dev_name)
            lib_names = get_lib_names(request.dev_name)
            config = json.loads(read_config(request.dev_name))
        basis = {
            'username': request.user.username,
            'email':
                request.user.email if request.user.is_authenticated() else '',
            'appNames': app_names,
            'libNames': lib_names,
            'config': config,
        }
        return render_to_response(
            'ide.html',
            {
                'DEBUG': DEBUG,
                'KAPPA_VERSION': KAPPA_VERSION,
                'basis': json.dumps(basis),
                'user': request.user,
            })


class ConfigHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')

    def get(self, request):
        return HttpResponse(
            read_config(request.dev_name), 'application/json; charset=utf-8')

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
            'From ' + (request.data['email'].strip() or 'anonym'),
            request.data['message'],
            None,
            ('info@akshell.com', 'main@akshell.flowdock.com',))
        return HttpResponse()


class AppsHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')

    def get(self, request):
        return get_app_names(request.dev_name)

    def post(self, request):
        app_name = request.data['name']
        check_name(app_name)
        create_app(request.dev_name, app_name)
        return HttpResponse(status=CREATED)
