# (c) 2010 by Anton Korenyushkin

import httplib
import urllib
from urlparse import urlparse
import shutil

import simplejson as json
from django.test import TestCase
from django.test.client import Client, FakePayload
from django.utils.http import urlencode

from paths import setup_paths


TEST_ROOT_PATH = '/tmp/chatlanian/'


class BaseTest(TestCase):
    def setUp(self):
        setup_paths(TEST_ROOT_PATH, True)
        self.client = Client()

    def tearDown(self):
        shutil.rmtree(TEST_ROOT_PATH)

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

    def get(self, path, data=None, status=httplib.OK):
        if data:
            path += '?' + urlencode(data, True)
        return self.request('GET', path, status=status)

    def post(self, path, data='', content_type=None, status=httplib.CREATED):
        if not isinstance(data, str):
            data = json.dumps(data)
            content_type = 'application/json'
        return self.request('POST', path, data, content_type, status)

    def put(self, path, data='', content_type=None, status=httplib.OK):
        return self.request('PUT', path, data, content_type, status)


class BasicTest(BaseTest):
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


class DevTest(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)
        self.post(
            'signup',
            {'name': 'bob', 'email': 'bob@xxx.com', 'password': 'xxx'})

    def test_config(self):
        self.assertEqual(self.get('config'), {})
        self.put('config', '{"x":42}', 'application/json')
        self.assertEqual(self.get('config'), {'x': 42})
        self.put('config', 'bad', 'application/json', httplib.BAD_REQUEST)
        self.put('config', '<x>42</x>', 'text/xml', httplib.BAD_REQUEST)

    def test_rsa_pub(self):
        self.assert_(self.get('rsa.pub').startswith('ssh-rsa '))
