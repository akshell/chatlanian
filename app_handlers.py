# (c) 2010 by Anton Korenyushkin

from __future__ import with_statement
from httplib import CREATED, NOT_FOUND
import re
import os
import shutil
import errno
import mimetypes

import simplejson as json
from piston.handler import BaseHandler
from piston.utils import require_mime
from django.http import HttpResponse

from error import Error
from utils import check_name, read_file, write_file, get_id, execute_sql
from paths import LOCKS_PATH, TMP_PATH, DEVS_PATH, DOMAINS_PATH
from managers import CREATE_SCHEMA_SQL, send_to_ecilop, stop_patsaks
from git import parse_git_command, run_git


def _getting_app_path(func):
    def result(self, request, app_name, **kwargs):
        app_path = DEVS_PATH[request.dev_name].apps[app_name]
        if not os.path.exists(app_path):
            raise Error(
                'The app "%s" doesn\'t exist.' % app_name, status=NOT_FOUND)
        return func(self, request, app_name, app_path=app_path, **kwargs)
    return result


class AppHandler(BaseHandler):
    allowed_methods = ('DELETE')

    @_getting_app_path
    def delete(self, request, app_name, app_path):
        app_id = get_id(request.dev_name, app_name)
        stop_patsaks(app_id)
        domains = json.loads(read_file(app_path.domains).lower())
        for domain in domains:
            os.remove(DOMAINS_PATH[domain])
        tmp_app_path = TMP_PATH[app_id]
        os.rename(app_path, tmp_app_path)
        shutil.rmtree(tmp_app_path)
        execute_sql('SELECT ak.drop_schemas(%s)', (app_id,))
        return HttpResponse()


_RELEASE_ENV_NAME = 'release'


def _get_absent_env_path(app_path, env_name):
    if env_name.lower() == _RELEASE_ENV_NAME:
        raise Error(
            'The environment name "%s" is reserved.' % _RELEASE_ENV_NAME,
            'Please choose another name.')
    env_path = app_path.envs[env_name]
    if os.path.exists(env_path):
        raise Error(
            'The environment "%s" already exists.' % read_file(env_path),
            'Environment name must be case-insensitively unique.')
    return env_path


class EnvsHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')

    @_getting_app_path
    def get(self, request, app_name, app_path):
        return [
            read_file(app_path.envs[lower_name])
            for lower_name in sorted(os.listdir(app_path.envs))
        ]

    @_getting_app_path
    def post(self, request, app_name, app_path):
        env_name = request.data['name']
        check_name(env_name)
        env_path = _get_absent_env_path(app_path, env_name)
        execute_sql(
            CREATE_SCHEMA_SQL, (get_id(request.dev_name, app_name, env_name),))
        write_file(env_path, env_name)
        return HttpResponse(status=CREATED)


def _get_existent_env_path(app_path, env_name):
    env_path = app_path.envs[env_name]
    if not os.path.exists(env_path):
        raise Error(
            'The environment "%s" doesn\'t exist.' % env_name, status=NOT_FOUND)
    return env_path


class EnvHandler(BaseHandler):
    allowed_methods = ('POST', 'DELETE')

    @_getting_app_path
    def post(self, request, app_name, env_name, app_path):
        action = request.data['action']
        if action == 'rename':
            env_path = _get_existent_env_path(app_path, env_name)
            new_env_name = request.data['name']
            check_name(new_env_name)
            new_env_path = _get_absent_env_path(app_path, new_env_name)
            stop_patsaks(get_id(request.dev_name, app_name, env_name))
            write_file(new_env_path, new_env_name)
            schema_prefix = get_id(request.dev_name, app_name) + ':'
            execute_sql(
                'SELECT ak.rename_schema(%s, %s)',
                (schema_prefix + env_name.lower(),
                 schema_prefix + new_env_name.lower()))
            os.remove(env_path)
            return HttpResponse()
        if action == 'eval':
            request.lock.release()
            request.lock = None
            if env_name == _RELEASE_ENV_NAME:
                env_name = None
            response = send_to_ecilop(
                'EVAL ' + get_id(request.dev_name, app_name, env_name),
                request.data['expr'])
            assert response
            status = response[0]
            result = response[1:]
            assert status in ('E', 'F', 'S')
            if status == 'E':
                raise Error(result, status=NOT_FOUND)
            return {'ok': status == 'S', 'result': result}
        raise Error('Unknown action: "%s"' % action)

    @_getting_app_path
    def delete(self, request, app_name, env_name, app_path):
        env_path = _get_existent_env_path(app_path, env_name)
        stop_patsaks(get_id(request.dev_name, app_name, env_name))
        os.remove(env_path)
        execute_sql(
            'SELECT ak.drop_schema(%s)',
            (get_id(request.dev_name, app_name, env_name),))
        return HttpResponse()


_DOMAIN_RE = re.compile(r'^(?:[a-z0-9](?:-*[a-z0-9])*\.)+[a-z]+$')
_AKSHELL_SUFFIX = '.akshell.com'


class DomainsHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')

    @_getting_app_path
    def get(self, request, app_name, app_path):
        return HttpResponse(
            read_file(app_path.domains), 'application/json; charset=utf-8')

    @require_mime('json')
    @_getting_app_path
    def put(self, request, app_name, app_path):
        domains_lower = set(json.loads(read_file(app_path.domains).lower()))
        new_domains = []
        new_domains_lower = set()
        has_akshell = False
        with LOCKS_PATH.domains.acquire_exclusive():
            for new_domain in request.data:
                new_domain_lower = new_domain.lower()
                if new_domain_lower in new_domains_lower:
                    continue
                if not _DOMAIN_RE.match(new_domain_lower):
                    raise Error(
                        '"%s" is not a valid domain name.' % new_domain, '''\
Domain name must consist of two or more parts separated by dots. \
Each part must consist of Latin letters, digits, and hyphens; \
it must not start or end with a hyphen.''')
                if new_domain_lower.endswith(_AKSHELL_SUFFIX):
                    if has_akshell:
                        raise Error(
                            'Only one akshell.com subdomain is provided.')
                    has_akshell = True
                    if new_domain_lower.count('.', 0, -len(_AKSHELL_SUFFIX)):
                        raise Error('''\
Name of akshell.com subdomain must not contain dots.''')
                if (new_domain_lower not in domains_lower
                    and os.path.exists(DOMAINS_PATH[new_domain_lower])):
                    raise Error(
                        ('The domain "%s" is bound to other application.'
                         % new_domain),
                        'Please choose another domain.')
                new_domains.append(new_domain)
                new_domains_lower.add(new_domain_lower)
            app_id = get_id(request.dev_name, app_name)
            stop_patsaks(app_id)
            for new_domain_lower in new_domains_lower.difference(domains_lower):
                write_file(DOMAINS_PATH[new_domain_lower], app_id)
            for old_domain_lower in domains_lower.difference(new_domains_lower):
                os.remove(DOMAINS_PATH[old_domain_lower])
        write_file(app_path.domains, json.dumps(new_domains))
        return HttpResponse()


def _traverse(path):
    result = {}
    for name in os.listdir(path):
        child_path = path + '/' + name
        result[name] = (
            _traverse(child_path) if os.path.isdir(child_path) else None)
    return result


def _check_path(path, can_be_empty=False):
    parts = [part for part in path.split('/') if part]
    if '.' in parts or '..' in parts or not (parts or can_be_empty):
        raise Error('The path "%s" is incorrect.' % path, '''\
Path must be non-empty and must not contain the "." and ".." components.''')
    return parts


class CodeHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')

    @_getting_app_path
    def get(self, request, app_name, app_path):
        return _traverse(app_path.code)

    @_getting_app_path
    def post(self, request, app_name, app_path):
        stop_patsaks(get_id(request.dev_name, app_name) + ':')
        prefix = app_path.code + '/'
        action = request.data['action']
        if action == 'mkdir':
            path = request.data['path']
            _check_path(path)
            try:
                os.makedirs(prefix + path)
            except OSError, error:
                assert error.errno == errno.EEXIST
                raise Error('The entry "%s" already exists.' % path,
                            'Please choose another name.')
            return HttpResponse(status=CREATED)
        if action == 'rm':
            paths = request.data['paths']
            for path in paths:
                _check_path(path)
            for path in paths:
                abs_path = prefix + path
                try:
                    os.remove(abs_path)
                except OSError, error:
                    if error.errno == errno.EISDIR:
                        shutil.rmtree(abs_path)
        elif action == 'mv':
            src_paths = request.data['srcPaths']
            dst_path = request.data['dstPath']
            src_names = [_check_path(src_path)[-1] for src_path in src_paths]
            _check_path(dst_path, True)
            dst_prefix = prefix + dst_path + '/'
            if not os.path.isdir(dst_prefix):
                raise Error('The folder "%s" doesn\'t exist.' % dst_path,
                            status=NOT_FOUND)
            failed_paths = []
            for src_path, src_name in zip(src_paths, src_names):
                try:
                    os.rename(prefix + src_path, dst_prefix + src_name)
                except OSError:
                    failed_paths.append(src_path)
            if failed_paths:
                raise Error('Failed to move the entries "%s".'
                            % '", "'.join(failed_paths))
        else:
            raise Error('Unknown action: "%s"' % action)
        return HttpResponse()


class FileHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')

    @_getting_app_path
    def get(self, request, app_name, app_path, path):
        _check_path(path)
        try:
            content = read_file(app_path.code + '/' + path)
        except IOError, error:
            raise (Error('"%s" is a folder.' % path)
                   if error.errno == errno.EISDIR else
                   Error('The file "%s" doesn\'t exist.' % path,
                         status=NOT_FOUND))
        return HttpResponse(content, mimetypes.guess_type(path)[0])

    @_getting_app_path
    def put(self, request, app_name, app_path, path):
        stop_patsaks(get_id(request.dev_name, app_name) + ':')
        parts = _check_path(path)
        try:
            write_file(app_path.code + '/' + path, request.raw_post_data)
        except IOError, error:
            raise (
                Error('"%s" is a folder.' % path)
                if error.errno == errno.EISDIR else
                Error('The folder "%s" doesn\'t exist.' % '/'.join(parts[:-1]),
                      status=NOT_FOUND))
        return HttpResponse()


class GitHandler(BaseHandler):
    allowed_methods = ('POST')

    @_getting_app_path
    def post(self, request, app_name, app_path):
        command, args = parse_git_command(request.user, request.data['command'])
        host_id = get_id(request.dev_name, app_name)
        if command not in (
            'commit', 'merge', 'pull', 'rebase', 'reset', 'revert'):
            host_id += ':'
        stop_patsaks(host_id)
        return HttpResponse(
            run_git(request.dev_name, app_name, command, *args),
            'text/plain; charset=utf-8')


class PublicHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')

    @_getting_app_path
    def get(self, request, app_name, app_path):
        return os.path.exists(DEVS_PATH[request.dev_name].libs[app_name])

    @_getting_app_path
    def put(self, request, app_name, app_path):
        lib_path = DEVS_PATH[request.dev_name].libs[app_name]
        if request.data:
            try:
                os.symlink(app_path, lib_path)
            except OSError, error:
                assert error.errno == errno.EEXIST
        else:
            try:
                os.remove(lib_path)
            except OSError, error:
                assert error.errno == errno.ENOENT
