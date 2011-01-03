# (c) 2010-2011 by Anton Korenyushkin

from httplib import BAD_REQUEST

import simplejson as json
from piston.utils import HttpStatusCode
from django.http import HttpResponse


class Error(HttpStatusCode):
    def __init__(self, message, comment='', status=BAD_REQUEST):
        HttpStatusCode.__init__(
            self,
            HttpResponse(
                json.dumps({'message': message, 'comment': comment}),
                'application/json; charset=utf-8',
                status))
