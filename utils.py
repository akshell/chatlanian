# (c) 2010 by Anton Korenyushkin

import re
import httplib

from piston.resource import Resource
from django.http import HttpResponse

from error import Error


class DjangoAuth(object):
    def is_authenticated(self, request):
        return request.user.is_authenticated()

    def challenge(self):
        return HttpResponse(status=httplib.UNAUTHORIZED)


django_auth = DjangoAuth()


def make_resource(handler_class):
    return Resource(handler_class, django_auth)


NAME_RE = re.compile('^%(w)s(?:%(w)s|-%(w)s)*$' % {'w': '[a-zA-Z0-9]'})


def check_name(name):
    if not NAME_RE.match(name):
        raise Error(
            'The name "%s" is incorrect.' % name,
            ('Name must consist of Latin letters, digits, and single hyphens.' +
             'It must not start or end with a hyphen.'))
