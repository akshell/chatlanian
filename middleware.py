# (c) 2010 by Anton Korenyushkin

import httplib

from django.http import HttpResponse


class AjaxMiddleware(object):
    def process_request(self, request):
        if not request.is_ajax():
            return HttpResponse('Non-AJAX request', status=httplib.FORBIDDEN)
