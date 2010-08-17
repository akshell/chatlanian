# (c) 2010 by Anton Korenyushkin

import httplib
import urllib
from urlparse import urlparse

import simplejson as json
from django.test import TestCase
from django.test.client import Client, FakePayload


class Test(TestCase):
    def setUp(self):
        self.client = Client()

    def request(self, method, path, data='', content_type=None,
                status=httplib.OK):
        if not path.startswith('/'):
            path = '/' + path
        parsed = urlparse(path)
        request = {
            'REQUEST_METHOD': method,
            'PATH_INFO': urllib.unquote(parsed[2]),
            'QUERY_STRING': parsed[4],
            'wsgi.input': FakePayload(data),
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
        }
        if data:
            request['CONTENT_LENGTH'] = len(data)
        if content_type:
            request['CONTENT_TYPE'] = content_type
        response = self.client.request(**request)
        self.assertEqual(response.status_code, status, response.content)
        return (json.loads(response.content)
                if response['Content-Type'] == 'application/json' else
                response.content)

    def post(self, path, data='', content_type=None, status=httplib.CREATED):
        if not isinstance(data, str):
            data = json.dumps(data)
            content_type = 'application/json'
        return self.request('POST', path, data, content_type, status)

    def test_ajax_middleware(self):
        self.assertEqual(self.client.get('/').status_code, httplib.FORBIDDEN)

    def test_auth(self):
        self.post(
            'signup',
            {'name': 'bob', 'email': 'bob@xxx.com', 'password': 'xxx'})
        self.post(
            'login',
            {'name': 'bob', 'password': 'xxx'},
            status=httplib.METHOD_NOT_ALLOWED)
        self.post('logout', status=httplib.OK)
        self.post('logout', status=httplib.UNAUTHORIZED)
        self.post(
            'signup',
            {'name': 'Bob', 'email': 'bob@yyy.com', 'password': 'yyy'},
            status=httplib.BAD_REQUEST)
        self.post(
            'signup',
            {'name': 'alice', 'email': 'bad', 'password': 'xxx'},
            status=httplib.BAD_REQUEST)
        self.post(
            'signup',
            {'name': 'bobby', 'email': 'bob@xxx.com', 'password': 'xxx'},
            status=httplib.BAD_REQUEST)
        self.post(
            'signup',
            {'name': 'x' * 31, 'email': 'x@xxx.com', 'password': 'xxx'},
            status=httplib.BAD_REQUEST)
        self.post(
            'login',
            {'name': 'bob', 'password': 'bad'},
            status=httplib.BAD_REQUEST)
        self.post(
            'login',
            {'name': 'bad', 'password': 'xxx'},
            status=httplib.BAD_REQUEST)
        self.post(
            'login',
            {'name': 'bob', 'password': 'xxx'},
            status=httplib.OK)
        self.client.logout()
        self.post(
            'signup',
            {'name': 'In--correct', 'email': 'a@xxx.com', 'password': 'xxx'},
            status=httplib.BAD_REQUEST)
        self.post(
            'signup',
            {'name': 'Ho-Shi-Min', 'email': 'ho@shi.min', 'password': 'xxx'})
        self.client.logout()
        self.post(
            'login',
            {'name': 'Ho Shi Min', 'password': 'xxx'},
            status=httplib.OK)
