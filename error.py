# (c) 2010 by Anton Korenyushkin

import httplib

import simplejson as json
from piston.utils import HttpStatusCode
from django.http import HttpResponse


class Error(HttpStatusCode):
    def __init__(self, message, comment='', status=httplib.BAD_REQUEST):
        HttpStatusCode.__init__(
            self,
            HttpResponse(
                json.dumps({'message': message, 'comment': comment}),
                'application/json; charset=utf-8',
                status))
