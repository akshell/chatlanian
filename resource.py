# (c) 2010 by Anton Korenyushkin

from httplib import UNAUTHORIZED, FORBIDDEN

from piston.resource import Resource as PistonResource
from django.http import HttpResponse

from paths import ANONYM_NAME, ROOT
from managers import create_dev


ANONYMOUS, GET_ANONYMOUS, HALF_ANONYMOUS, AUTHENTICATED = range(4)

_CHARSET_SUFFIX = '; charset=utf-8'


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
        if request.raw_post_data:
            content_type = request.META.get('CONTENT_TYPE', '')
            if content_type.lower().endswith(_CHARSET_SUFFIX):
                request.META['CONTENT_TYPE'] = content_type[:-len(_CHARSET_SUFFIX)]
        else:
            request.META.pop('CONTENT_TYPE', None)
        request.is_anonymous = request.is_half_anonymous = False
        if request.user.is_authenticated():
            request.dev_name = request.user.username
        else:
            access = getattr(self.handler, 'access', GET_ANONYMOUS)
            if access == AUTHENTICATED:
                return HttpResponse('Authentication required', status=UNAUTHORIZED)
            try:
                request.dev_name = request.session['dev_name']
            except KeyError:
                if (access == HALF_ANONYMOUS or
                    access == GET_ANONYMOUS and request.method != 'GET'):
                    request.dev_name = request.session['dev_name'] = (
                        create_dev())
                else:
                    request.dev_name = ANONYM_NAME
                    request.is_anonymous = True
            request.is_half_anonymous = not request.is_anonymous
        if not request.is_anonymous:
            lock_path = ROOT.locks[request.dev_name]
            request.lock = (
                lock_path.acquire_shared() if request.method == 'GET' else
                lock_path.acquire_exclusive())
        else:
            request.lock = None
        try:
            return PistonResource.__call__(self, request, *args, **kwargs)
        finally:
            if request.lock:
                request.lock.release()
