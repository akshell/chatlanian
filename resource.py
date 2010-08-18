# (c) 2010 by Anton Korenyushkin

import fcntl
import httplib

from piston.resource import Resource as PistonResource
from django.http import HttpResponse

from paths import get_lock_path


class Authentication(object):
    def is_authenticated(self, request):
        return request.user.is_authenticated()

    def challenge(self):
        return HttpResponse(status=httplib.UNAUTHORIZED)


authentication = Authentication()


class Resource(PistonResource):
    def __init__(self, handler):
        PistonResource.__init__(self, handler, authentication)

    def __call__(self, request, *args, **kwargs):
        if request.method != 'GET' and not request.is_ajax():
            return HttpResponse('Non-AJAX request', status=httplib.FORBIDDEN)
        if request.user.is_authenticated():
            f = open(get_lock_path(request.user.username))
            fcntl.flock(
                f, fcntl.LOCK_SH if request.method == 'GET' else fcntl.LOCK_EX)
        else:
            f = None
        try:
            return PistonResource.__call__(self, request, *args, **kwargs)
        finally:
            if f:
                f.close()
