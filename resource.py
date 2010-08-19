# (c) 2010 by Anton Korenyushkin

import fcntl
import httplib

from piston.resource import Resource as PistonResource
from django.http import HttpResponse

from paths import ANONYM_NAME, locks_path, create_dev


class Authentication(object):
    def is_authenticated(self, request):
        return True


authentication = Authentication()


class Resource(PistonResource):
    def __init__(self, handler):
        PistonResource.__init__(self, handler, authentication)

    def __call__(self, request, *args, **kwargs):
        if request.method != 'GET' and not request.is_ajax():
            return HttpResponse('Non-AJAX request', status=httplib.FORBIDDEN)
        request.is_anonymous = request.is_half_anonymous = False
        if request.user.is_authenticated():
            request.dev_name = request.user.username
        else:
            try:
                request.dev_name = request.session['dev_name']
            except KeyError:
                handles_anonyms = getattr(self.handler, 'handles_anonyms', None)
                if (handles_anonyms is False or
                    handles_anonyms is None and request.method != 'GET'):
                    request.dev_name = request.session['dev_name'] = (
                        create_dev())
                else:
                    request.dev_name = ANONYM_NAME
                    request.is_anonymous = True
            request.is_half_anonymous = not request.is_anonymous
        if not request.is_anonymous:
            f = open(locks_path[request.dev_name])
            fcntl.flock(
                f, fcntl.LOCK_SH if request.method == 'GET' else fcntl.LOCK_EX)
        else:
            f = None
        try:
            return PistonResource.__call__(self, request, *args, **kwargs)
        finally:
            if f:
                f.close()
