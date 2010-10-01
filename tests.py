# (c) 2010 by Anton Korenyushkin

from httplib import (
    OK, CREATED, FOUND, BAD_REQUEST, UNAUTHORIZED, FORBIDDEN, NOT_FOUND)
from subprocess import Popen
from urlparse import urlparse
import urllib
import shutil
import os

import simplejson as json
from django.test import TestCase
from django.test.client import Client, FakePayload
from django.db import connection

from paths import ANONYM_NAME, ROOT, create_paths
from utils import execute_sql
import auth_handlers
import dev_handlers


_last_email_subject = None
_last_email_message = None

def _send_mail(subject, message, from_email, recipient_list):
    global _last_email_subject, _last_email_message
    _last_email_subject = subject
    _last_email_message = message

auth_handlers.send_mail = dev_handlers.send_mail = _send_mail



class BaseTest(TestCase):
    def setUp(self):
        create_paths()
        self.client = Client()
        connection._set_isolation_level(0)

    def tearDown(self):
        execute_sql('SELECT ak.drop_all_schemas()')
        for dev_name in os.listdir(ROOT.devs):
            if dev_name != ANONYM_NAME:
                execute_sql('DROP TABLESPACE "%s"' % dev_name)
        Popen('sudo rm -r %s %s' % (ROOT.devs, ROOT.trash), shell=True)
        shutil.rmtree(ROOT.locks)
        shutil.rmtree(ROOT.domains)

    def request(self, method, path, data='', content_type=None, status=OK):
        if not path.startswith('/'):
            path = '/' + path
        if not isinstance(data, str):
            data = json.dumps(data)
            content_type = content_type or 'application/json'
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
                if response['Content-Type'].startswith('application/json') else
                response.content)

    def get(self, path, status=OK):
        return self.request('GET', path, status=status)

    def post(self, path, data='', content_type=None, status=OK):
        return self.request('POST', path, data, content_type, status)

    def put(self, path, data='', content_type=None, status=OK):
        return self.request('PUT', path, data, content_type, status)

    def delete(self, path, status=OK):
        return self.request('DELETE', path, status=status)


class BasicTest(BaseTest):
    def test_misc(self):
        self.get('')
        self.assertEqual(self.client.post('/signup').status_code, FORBIDDEN)
        self.get('no/such/page', status=NOT_FOUND)
        self.get('rsa.pub')
        self.get('')
        self.post('/contact', {'email': 'x@y.com  ', 'message': 'wuzzup'})
        self.assertEqual(_last_email_subject, 'From x@y.com')
        self.assertEqual(_last_email_message, 'wuzzup')
        self.post('/contact', {'email': ' ', 'message': 'yo'})
        self.assertEqual(_last_email_subject, 'From anonym')
        self.assertEqual(_last_email_message, 'yo')

    def test_auth(self):
        self.post(
            'signup',
            {'name': 'bob', 'email': 'bob@xxx.com', 'password': 'xxx'},
            status=CREATED)
        self.put('/config', {'x': 42})
        self.post('/apps/', {'name': 'blog'}, status=CREATED)
        self.post(
            'signup',
            {'name': 'mary', 'email': 'mary@yyy.com', 'password': 'yyy'},
            content_type='application/json; charset=UTF-8',
            status=CREATED)
        self.post('logout', content_type='text/plain')
        self.post('logout', status=UNAUTHORIZED)
        self.post(
            'signup',
            {'name': 'Bob', 'email': 'bob@yyy.com', 'password': 'yyy'},
            status=BAD_REQUEST)
        self.post(
            'signup',
            {'name': 'alice', 'email': 'bad', 'password': 'xxx'},
            status=BAD_REQUEST)
        self.post(
            'signup',
            {'name': 'bobby', 'email': 'bob@xxx.com', 'password': 'xxx'},
            status=BAD_REQUEST)
        self.post(
            'signup',
            {'name': 'x' * 31, 'email': 'x@xxx.com', 'password': 'xxx'},
            status=BAD_REQUEST)
        self.post(
            'signup',
            {'name': 'anonym42', 'email': 'anonym@xxx.com', 'password': 'xxx'},
            status=BAD_REQUEST)
        self.post(
            'login',
            {'name': 'bob', 'password': 'bad'},
            status=BAD_REQUEST)
        self.post(
            'login',
            {'name': 'bad', 'password': 'xxx'},
            status=BAD_REQUEST)
        self.assertEqual(
            self.post('login', {'name': 'bob', 'password': 'xxx'}),
            {
                'email': 'bob@xxx.com',
                'appNames': ['blog', 'hello-world'],
                'config': {'x': 42},
            })
        self.client.logout()
        self.post(
            'signup',
            {'name': 'In--correct', 'email': 'a@xxx.com', 'password': 'xxx'},
            status=BAD_REQUEST)
        self.get('rsa.pub')
        self.post(
            'signup',
            {'name': 'Ho-Shi-Min', 'email': 'ho@shi.min', 'password': 'xxx'},
            status=CREATED)
        self.post('password', {'old': 'bad', 'new': 'yyy'}, status=BAD_REQUEST)
        self.post('password', {'old': 'xxx', 'new': 'zzz'})
        self.client.logout()
        self.get('rsa.pub')
        self.post('login', {'name': 'Ho Shi Min', 'password': 'zzz'})
        self.client.logout()
        self.post('password', {'name': 'bad'}, status=BAD_REQUEST)
        self.post('password', {'email': 'bad'}, status=BAD_REQUEST)
        self.get('password/bad-bad', status=NOT_FOUND)
        self.post('password', {'name': 'ho shi min'})
        self.post('password', {'email': 'bob@xxx.com'})
        path = _last_email_message.split('\n')[4][23:]
        self.get(path)
        self.post(path, 'new=yyy', status=FOUND)
        self.post('login', {'name': 'bob', 'password': 'yyy'})


class DevTest(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)
        self.post(
            'signup',
            {'name': 'bob', 'email': 'bob@xxx.com', 'password': 'xxx'},
            status=CREATED)

    def test_config(self):
        self.assertEqual(self.get('config'), {})
        self.put('config', {'x': 42})
        self.assertEqual(self.get('config'), {'x': 42})
        self.put('config', 'bad', 'application/json', BAD_REQUEST)
        self.put('config', '<x>42</x>', 'text/xml', BAD_REQUEST)
        self.client.logout()
        self.assertEqual(self.get('config'), {})

    def test_rsa_pub(self):
        self.assertEqual(self.get('rsa.pub'), 'public key')

    def test_apps(self):
        self.post('apps/', {'name': 'Yo'}, status=CREATED)
        self.assertEqual(self.get('apps/'), ['hello-world', 'Yo'])
        self.post('apps/', {'name': 'yo'}, status=BAD_REQUEST)
        self.client.logout()
        self.assertEqual(self.get('apps/'), ['hello-world'])
        self.get('rsa.pub')
        self.assertEqual(self.get('apps/'), ['hello-world'])


class AppTest(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)
        self.post(
            'signup',
            {'name': 'bob', 'email': 'bob@xxx.com', 'password': 'xxx'},
            status=CREATED)
        self.post('apps/', {'name': 'Blog'}, status=CREATED)

    def test_delete_app(self):
        self.delete('apps/Blog/')
        self.delete('apps/Hello-World/')
        self.delete('apps/no-such-app/', status=NOT_FOUND)

    def test_envs(self):
        self.assertEqual(self.get('apps/blog/envs/'), ['debug'])
        self.post('apps/blog/envs/', {'name': 'Test'}, status=CREATED)
        self.assertEqual(self.get('apps/blog/envs/'), ['debug', 'Test'])
        def rename(name, new_name, status):
            self.post(
                'apps/blog/envs/' + name,
                {'action': 'rename', 'name': new_name},
                status=status)
        rename('debug', 'test', BAD_REQUEST)
        self.post('apps/blog/envs/', {'name': 'Debug'}, status=BAD_REQUEST)
        self.post('apps/blog/envs/', {'name': 'Release'}, status=BAD_REQUEST)
        self.delete('apps/blog/envs/Debug')
        self.delete('apps/blog/envs/no-such', status=NOT_FOUND)
        self.assertEqual(self.get('apps/blog/envs/'), ['Test'])
        rename('test', 'bad!', BAD_REQUEST)
        rename('no-such', 'xxx', NOT_FOUND)
        rename('test', 'Debug', OK)
        self.assertEqual(self.get('apps/blog/envs/'), ['Debug'])
        response = self.post(
            'apps/blog/envs/release', {'action': 'eval', 'expr': '1'})
        self.assert_(not response['ok'])
        self.assert_(response['result'].startswith('RequireError:'))
        self.put('apps/blog/code/main.js', 'x = 42')
        response = self.post(
            'apps/blog/envs/debug', {'action': 'eval', 'expr': 'x'})
        self.assert_(response['ok'])
        self.assertEqual(response['result'], '42')
        self.post(
            'apps/blog/envs/no-such', {'action': 'eval', 'expr': '1'},
            status=NOT_FOUND)
        self.post('apps/blog/envs/debug', {'action': 'bad'}, status=BAD_REQUEST)

    def test_domains(self):
        path = 'apps/blog/domains'
        self.assertEqual(self.get(path), [])
        self.put(path, ['blog.akshell.com', 'MyBlog.com', 'myblog.com'])
        self.assertEqual(self.get(path), ['blog.akshell.com', 'MyBlog.com'])
        self.put(path, ['Blog.akshell.com', 'yo.wuzzup.com', '111.ru'])
        self.put(path, ['bad!'], status=BAD_REQUEST)
        self.put(path, ['1.akshell.com', '2.akshell.com'], status=BAD_REQUEST)
        self.put(path, ['1.2.akshell.com'], status=BAD_REQUEST)
        self.post('apps/', {'name': 'Forum'}, status=CREATED)
        self.put('apps/forum/domains', ['forum.akshell.com', 'myforum.com'])
        self.put(path, ['forum.akshell.com'], status=BAD_REQUEST)
        self.put(path, ['blog.myforum.com'], status=BAD_REQUEST)
        self.delete('apps/blog/')

    def test_code(self):
        path = 'apps/blog/code/'
        self.assertEqual(
            self.get(path),
            {
                'templates': {
                    'index.html': None,
                    'base.html': None,
                    'error.html': None,
                },
                'static': {'base.css': None},
                'main.js': None,
            })
        self.post(
            path,
            {
                'action': 'rm',
                'paths': ['templates', '/static//base.css', 'no/such'],
            })
        self.assertEqual(self.get(path), {'static': {}, 'main.js': None})
        self.put(path + 'static/hello.txt', 'Hello world')
        self.assertEqual(self.get(path + '//static/hello.txt'), 'Hello world')
        self.post(path, {'action': 'mkdir', 'path': 'a/b/c'}, status=CREATED)
        self.post(
            path,
            {
                'action': 'mv',
                'srcPaths': ['a/b', 'main.js'],
                'dstPath': 'static',
            })
        self.assertEqual(
            self.get(path),
            {
                'a': {},
                'static': {'b': {'c': {}}, 'main.js': None, 'hello.txt': None},
            })
        self.post(
            path, {'action': 'mkdir', 'path': 'x/../y'}, status=BAD_REQUEST)
        self.get(path + '/', status=BAD_REQUEST)
        self.post(
            path, {'action': 'mkdir', 'path': 'static'}, status=BAD_REQUEST)
        self.post(
            path, {'action': 'mv', 'srcPaths': ['a'], 'dstPath': 'no/such'},
            status=NOT_FOUND)
        self.post(
            path,
            {
                'action': 'mv',
                'srcPaths': ['no/such', 'static/hello.txt'],
                'dstPath': '',
            },
            status=BAD_REQUEST)
        self.post(path, {'action': 'rm', 'paths': ['static']})
        self.assertEqual(self.get(path), {'a': {}, 'hello.txt': None})
        self.get(path + 'no/such', status=NOT_FOUND)
        self.put(path + 'no/such', '', status=NOT_FOUND)
        self.get(path + 'a', status=BAD_REQUEST)
        self.put(path + 'a', '', status=BAD_REQUEST)
        self.post(path, {'action': 'bad'}, status=BAD_REQUEST)

    def test_git(self):
        def run(command, valid=True):
            return self.post(
                'apps/blog/git', {'command': command},
                status=OK if valid else BAD_REQUEST)
        run('help')
        run('help push')
        run('help clone', False)
        run('init xxx', False)
        run('remote add origin gopher://example.com', False)
        run('push ../bad/path', False)
        run('clean --bad', False)
        self.assert_('Initial commit.' in run('log'))
        self.put('apps/blog/code/static/hello.txt', 'Hello world')
        self.assert_('static/hello.txt' in run('status'))
        run('add static/hello.txt')
        run('commit -m "Hello git!"')
        full_log = run('log -u -n1')
        self.assert_('Hello git' in full_log)
        self.assert_('Hello world' in full_log)
        run('tag -a bad', False)
        run('tag -l')
        run('tag -am hello')
        run('tag hi')

    def test_public(self):
        self.assertEqual(self.get('apps/blog/public'), False)
        self.put('apps/blog/public', True)
        self.put('apps/blog/public', True)
        self.assertEqual(self.get('apps/blog/public'), True)
        self.put('apps/blog/public', False)
        self.put('apps/blog/public', False)
        self.assertEqual(self.get('apps/blog/public'), False)


class LibTest(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)
        self.post(
            'signup',
            {'name': 'bob', 'email': 'bob@xxx.com', 'password': 'xxx'},
            status=CREATED)
        self.post('apps/', {'name': 'Lib'}, status=CREATED)
        self.put('apps/lib/public', True)
        self.put('apps/lib/code/hello.txt', 'Hello world')
        for command in (
            'tag -am "First tag" xxx',
            'add hello.txt',
            'commit -m "Second commit."',
            'branch xxx',
        ):
            self.post('apps/lib/git', {'command': command})

    def test_lib(self):
        self.assertEqual(self.get('libs/bob/'), ['hello-world', 'Lib'])
        self.get('libs/no-such-dev/', status=NOT_FOUND)
        self.assertEqual(self.get('libs/bob/lib/'), ['HEAD', 'master', 'xxx'])
        self.get('libs/bob/no-such-lib/', status=NOT_FOUND)
        self.assertEqual(
            self.get('libs/bob/lib/master/'),
            {
                'templates': {
                    'index.html': None,
                    'base.html': None,
                    'error.html': None,
                },
                'static': {'base.css': None},
                'hello.txt': None,
                'main.js': None,
            })
        self.get('libs/bob/lib/no-such-version/', status=NOT_FOUND)
        self.assertEqual(
            self.get('libs/bob/lib/HEAD/hello.txt'), 'Hello world')
        self.get('libs/bob/lib/xxx/static/base.css')
        self.get('libs/bob/lib/master/main.js')
        self.get('libs/bob/lib/xxx/hello.txt', status=NOT_FOUND)
        self.get('libs/bob/lib/HEAD/main.js/no-such', status=NOT_FOUND)
        self.get('libs/bob/lib/master//main.js', status=NOT_FOUND)
        self.get('libs/bob/lib/xxx/templates', status=BAD_REQUEST)
        self.client.logout()
        self.assertEqual(self.get('libs/bob/'), ['Lib'])
