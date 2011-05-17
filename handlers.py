# (c) 2011 by Anton Korenyushkin

from piston.handler import BaseHandler
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.mail import send_mail

from settings import DEBUG
from paths import KAPPA_VERSION


class IDEHandler(BaseHandler):
    allowed_methods = ('GET',)

    def get(self, request):
        return render_to_response(
            'ide.html', {'DEBUG': DEBUG, 'KAPPA_VERSION': KAPPA_VERSION})


class ContactHandler(BaseHandler):
    allowed_methods = ('POST',)

    def post(self, request):
        send_mail(
            'From ' + (request.data['email'].strip() or 'anonym'),
            request.data['message'],
            None,
            ('info@akshell.com', 'main@akshell.flowdock.com',))
        return HttpResponse()
