# (c) 2010 by Anton Korenyushkin

from urlparse import urlparse
import httplib
import urllib
import shutil

import simplejson as json
from django.test import TestCase
from django.test.client import Client, FakePayload
from django.utils.http import urlencode

from paths import create_paths, LOCKS_PATH, DEVS_PATH, DOMAINS_PATH


class BaseTest(TestCase):
    def setUp(self):
        create_paths()
        self.client = Client()

    def tearDown(self):
        shutil.rmtree(LOCKS_PATH)
        shutil.rmtree(DEVS_PATH)
        shutil.rmtree(DOMAINS_PATH)

    def request(self, method, path, data='', content_type=None,
                status=httplib.OK):
        if not path.startswith('/'):
            path = '/' + path
        if not isinstance(data, str):
            data = json.dumps(data)
            content_type = 'application/json'
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

    def get(self, path, data=None, status=httplib.OK):
        if data:
            path += '?' + urlencode(data, True)
        return self.request('GET', path, status=status)

    def post(self, path, data='', content_type=None, status=httplib.OK):
        return self.request('POST', path, data, content_type, status)

    def put(self, path, data='', content_type=None, status=httplib.OK):
        return self.request('PUT', path, data, content_type, status)

    def delete(self, path, status=httplib.OK):
        return self.request('DELETE', path, status=status)


class BasicTest(BaseTest):
    def test_misc(self):
        self.assertEqual(
            self.client.post('/signup').status_code, httplib.FORBIDDEN)

    def test_auth(self):
        self.post(
            'signup',
            {'name': 'bob', 'email': 'bob@xxx.com', 'password': 'xxx'},
            status=httplib.CREATED)
        self.post(
            'signup',
            {'name': 'mary', 'email': 'mary@yyy.com', 'password': 'yyy'},
            status=httplib.CREATED)
        self.post('logout')
        self.post('logout')
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
            'signup',
            {'name': 'anonym42', 'email': 'anonym@xxx.com', 'password': 'xxx'},
            status=httplib.BAD_REQUEST)
        self.post(
            'login',
            {'name': 'bob', 'password': 'bad'},
            status=httplib.BAD_REQUEST)
        self.post(
            'login',
            {'name': 'bad', 'password': 'xxx'},
            status=httplib.BAD_REQUEST)
        self.post('login', {'name': 'bob', 'password': 'xxx'})
        self.client.logout()
        self.post(
            'signup',
            {'name': 'In--correct', 'email': 'a@xxx.com', 'password': 'xxx'},
            status=httplib.BAD_REQUEST)
        self.get('rsa.pub')
        self.post(
            'signup',
            {'name': 'Ho-Shi-Min', 'email': 'ho@shi.min', 'password': 'xxx'},
            status=httplib.CREATED)
        self.client.logout()
        self.get('rsa.pub')
        self.post('login', {'name': 'Ho Shi Min', 'password': 'xxx'})


class DevTest(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)
        self.post(
            'signup',
            {'name': 'bob', 'email': 'bob@xxx.com', 'password': 'xxx'},
            status=httplib.CREATED)

    def test_config(self):
        self.assertEqual(self.get('config'), {})
        self.put('config', {'x': 42})
        self.assertEqual(self.get('config'), {'x': 42})
        self.put('config', 'bad', 'application/json', httplib.BAD_REQUEST)
        self.put('config', '<x>42</x>', 'text/xml', httplib.BAD_REQUEST)
        self.client.logout()
        self.assertEqual(self.get('config'), {})

    def test_rsa_pub(self):
        self.assertEqual(self.get('rsa.pub'), 'public key')

    def test_apps(self):
        self.post('apps/', {'name': 'Yo'}, status=httplib.CREATED)
        self.assertEqual(self.get('apps/'), ['hello-world', 'Yo'])
        self.post('apps/', {'name': 'yo'}, status=httplib.BAD_REQUEST)
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
            status=httplib.CREATED)
        self.post('apps/', {'name': 'Blog'}, status=httplib.CREATED)

    def test_delete_app(self):
        self.delete('apps/Blog/')
        self.delete('apps/Hello-World/')
        self.delete('apps/no-such-app/', status=httplib.NOT_FOUND)

    def test_envs(self):
        self.assertEqual(self.get('apps/blog/envs/'), ['debug'])
        self.post('apps/blog/envs/', {'name': 'Test'}, status=httplib.CREATED)
        self.assertEqual(self.get('apps/blog/envs/'), ['debug', 'Test'])
        self.post(
            'apps/blog/envs/debug', {'name': 'test'},
            status=httplib.BAD_REQUEST)
        self.post(
            'apps/blog/envs/', {'name': 'Debug'},
            status=httplib.BAD_REQUEST)
        self.delete('apps/blog/envs/Debug')
        self.delete('apps/blog/envs/no-such', status=httplib.NOT_FOUND)
        self.assertEqual(self.get('apps/blog/envs/'), ['Test'])
        self.post(
            'apps/blog/envs/test', {'name': 'bad!'}, status=httplib.BAD_REQUEST)
        self.post(
            'apps/blog/envs/no-such', {'name': 'xxx'}, status=httplib.NOT_FOUND)
        self.post('apps/blog/envs/test', {'name': 'Debug'})
        self.assertEqual(self.get('apps/blog/envs/'), ['Debug'])

    def test_domains(self):
        path = 'apps/blog/domains'
        self.assertEqual(self.get(path), [])
        self.put(path, ['blog.akshell.com', 'MyBlog.com', 'myblog.com'])
        self.assertEqual(self.get(path), ['blog.akshell.com', 'MyBlog.com'])
        self.put(path, ['Blog.akshell.com', 'yo.wuzzup.com', '111.ru'])
        self.put(path, ['bad!'], status=httplib.BAD_REQUEST)
        self.put(
            path, ['1.akshell.com', '2.akshell.com'],
            status=httplib.BAD_REQUEST)
        self.put(path, ['1.2.akshell.com'], status=httplib.BAD_REQUEST)
        self.post('apps/', {'name': 'Forum'}, status=httplib.CREATED)
        self.put('apps/forum/domains', ['forum.akshell.com'])
        self.put(path, ['forum.akshell.com'], status=httplib.BAD_REQUEST)
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
        self.post(
            path, {'action': 'mkdir', 'path': 'a/b/c'}, status=httplib.CREATED)
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
            path, {'action': 'mkdir', 'path': 'x/../y'},
            status=httplib.BAD_REQUEST)
        self.get(path + '/', status=httplib.BAD_REQUEST)
        self.post(
            path, {'action': 'mkdir', 'path': 'static'},
            status=httplib.BAD_REQUEST)
        self.post(
            path, {'action': 'mv', 'srcPaths': ['a'], 'dstPath': 'no/such'},
            status=httplib.NOT_FOUND)
        self.post(
            path,
            {
                'action': 'mv',
                'srcPaths': ['no/such', 'static/hello.txt'],
                'dstPath': '',
            },
            status=httplib.BAD_REQUEST)
        self.post(path, {'action': 'rm', 'paths': ['static']})
        self.assertEqual(self.get(path), {'a': {}, 'hello.txt': None})
        self.get(path + 'no/such', status=httplib.NOT_FOUND)
        self.put(path + 'no/such', '', status=httplib.NOT_FOUND)
        self.get(path + 'a', status=httplib.BAD_REQUEST)
        self.put(path + 'a', '', status=httplib.BAD_REQUEST)
        self.post(path, {'action': 'bad'}, status=httplib.BAD_REQUEST)

    def test_git(self):
        def run(command, valid=True):
            return self.post(
                'apps/blog/git',
                {'command': command},
                status=httplib.OK if valid else httplib.BAD_REQUEST)
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
        run('tag -a', False)
        run('tag -l')
        run('tag -am hello')

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
            status=httplib.CREATED)
        self.post('apps/', {'name': 'Lib'}, status=httplib.CREATED)
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
        self.get('libs/no-such-dev/', status=httplib.NOT_FOUND)
        self.assertEqual(self.get('libs/bob/lib/'), ['HEAD', 'master', 'xxx'])
        self.get('libs/bob/no-such-lib/', status=httplib.NOT_FOUND)
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
        self.get('libs/bob/lib/no-such-version/', status=httplib.NOT_FOUND)
        self.assertEqual(
            self.get('libs/bob/lib/HEAD/hello.txt'), 'Hello world')
        self.get('libs/bob/lib/xxx/static/base.css')
        self.get('libs/bob/lib/master/main.js')
        self.get('libs/bob/lib/xxx/hello.txt', status=httplib.NOT_FOUND)
        self.get('libs/bob/lib/HEAD/main.js/no-such', status=httplib.NOT_FOUND)
        self.get('libs/bob/lib/master//main.js', status=httplib.NOT_FOUND)
        self.get('libs/bob/lib/xxx/templates', status=httplib.BAD_REQUEST)
        self.client.logout()
        self.assertEqual(self.get('libs/bob/'), ['Lib'])
