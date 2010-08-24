# (c) 2010 by Anton Korenyushkin

from httplib import FORBIDDEN

from piston.resource import Resource as PistonResource
from django.http import HttpResponse

from paths import ANONYM_NAME, LOCKS_PATH
from managers import create_dev


class Resource(PistonResource):
    callmap = {
        'GET': 'get',
        'POST': 'post',
        'PUT': 'put',
        'DELETE': 'delete',
    }

    def __call__(self, request, *args, **kwargs):
        if request.method != 'GET' and not request.is_ajax():
            return HttpResponse('Non-AJAX request', status=FORBIDDEN)
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
            lock_path = LOCKS_PATH[request.dev_name]
            lock = (lock_path.acquire_shared() if request.method == 'GET' else
                    lock_path.acquire_exclusive())
        else:
            lock = None
        try:
            return PistonResource.__call__(self, request, *args, **kwargs)
        finally:
            if lock:
                lock.release()
