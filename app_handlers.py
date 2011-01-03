# (c) 2010-2011 by Anton Korenyushkin

from __future__ import with_statement
from httplib import CREATED, NOT_FOUND
import re
import os
import shutil
import errno
import mimetypes
import socket

import simplejson as json
from piston.handler import BaseHandler
from piston.utils import require_mime
from django.http import HttpResponse

from settings import DEBUG, VARNISH_PORT
from error import Error
from utils import check_name, read_file, write_file, get_id, execute_sql
from paths import ROOT
from managers import CREATE_SCHEMA_SQL, send_to_ecilop, stop_patsaks
from git import parse_git_command, GitRunner
from resource import AUTHENTICATED


def _getting_app_path(func):
    def result(self, request, app_name, **kwargs):
        app_path = ROOT.devs[request.dev_name].apps[app_name]
        if not os.path.exists(app_path):
            raise Error(
                'The app "%s" doesn\'t exist.' % app_name, status=NOT_FOUND)
        return func(self, request, app_name, app_path=app_path, **kwargs)
    return result


def _purge_domains(domains):
    if DEBUG:
        return
    sock = socket.socket(socket.AF_INET)
    sock.connect(('127.0.0.1', VARNISH_PORT))
    sock.sendall(
        'PURGE / HTTP/1.1\r\nHost: "(?i)(%s)$"\r\n\r\n' % '|'.join(domains))
    sock.recv(8192)
    sock.close()


class AppHandler(BaseHandler):
    allowed_methods = ('DELETE')

    @_getting_app_path
    def delete(self, request, app_name, app_path):
        app_id = get_id(request.dev_name, app_name)
        stop_patsaks(app_id)
        domains = json.loads(read_file(app_path.domains).lower())
        _purge_domains(domains)
        for domain in domains:
            os.remove(ROOT.domains[domain])
        tmp_app_path = ROOT.tmp[app_id]
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


def _check_domain_is_free(domain):
    if os.path.exists(ROOT.domains[domain]):
        raise Error(
            'The domain "%s" is bound to other application.' % domain,
            'Please choose another domain.')


_DOMAIN_RE = re.compile(
    '^(%(p)s\.)?(%(p)s\.%(p)s)$' % {'p': '[a-z0-9](?:-*[a-z0-9])*'})

_AKSHELL_SUFFIX = '.akshell.com'


class DomainsHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')
    access = AUTHENTICATED

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
        with ROOT.locks.domains.acquire_exclusive():
            for new_domain in request.data:
                new_domain_lower = new_domain.lower()
                if new_domain_lower in new_domains_lower:
                    continue
                match = _DOMAIN_RE.match(new_domain_lower)
                if not match:
                    raise Error(
                        '"%s" is not a valid domain name.' % new_domain, '''\
Domain name must consist of two or three parts separated by dots. \
Each part must consist of Latin letters, digits, and hyphens; \
it must not start or end with a hyphen.''')
                if new_domain_lower.endswith(_AKSHELL_SUFFIX):
                    if has_akshell:
                        raise Error(
                            'Only one akshell.com subdomain is provided.')
                    has_akshell = True
                if new_domain_lower not in domains_lower:
                    _check_domain_is_free(new_domain_lower)
                if match.group(1) and match.group(2) not in domains_lower:
                    _check_domain_is_free(match.group(2))
                new_domains.append(new_domain)
                new_domains_lower.add(new_domain_lower)
            app_id = get_id(request.dev_name, app_name)
            stop_patsaks(app_id)
            for new_domain_lower in new_domains_lower.difference(domains_lower):
                write_file(ROOT.domains[new_domain_lower], app_id)
            old_domains_lower = domains_lower.difference(new_domains_lower)
            for old_domain_lower in old_domains_lower:
                os.remove(ROOT.domains[old_domain_lower])
        _purge_domains(old_domains_lower)
        write_file(app_path.domains, json.dumps(new_domains))
        return HttpResponse()


def _traverse(path):
    result = {}
    for name in os.listdir(path):
        child_path = path + '/' + name
        result[name] = (
            _traverse(child_path) if os.path.isdir(child_path) else None)
    return result


def _check_path(path):
    parts = [part for part in path.split('/') if part]
    if not parts or '.' in parts or '..' in parts:
        raise Error('The path "%s" is incorrect.' % path, '''\
Path must be non-empty and must not contain the "." and ".." components.''')
    return parts


def _remove_entry(path):
    try:
        os.remove(path)
    except OSError, error:
        if error.errno == errno.EISDIR:
            shutil.rmtree(path)


def _check_entry_exists(path):
    if not os.path.exists(path):
        raise EnvironmentError()


def _move_entry(src_path, dst_path):
    _check_entry_exists(src_path)
    _remove_entry(dst_path);
    os.rename(src_path, dst_path);


def _copy_entry(src_path, dst_path):
    _check_entry_exists(src_path)
    _remove_entry(dst_path)
    try:
        shutil.copyfile(src_path, dst_path)
    except IOError, error:
        if error.errno == errno.EISDIR:
            shutil.copytree(src_path, dst_path)
        else:
            raise


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
                _remove_entry(prefix + path)
        elif action in ('mv', 'cp'):
            path_pairs = request.data['pathPairs']
            func = _move_entry if action == 'mv' else _copy_entry
            failed_paths = []
            for path_pair in path_pairs:
                src_path, dst_path = path_pair
                _check_path(src_path)
                _check_path(dst_path)
                try:
                    func(prefix + src_path, prefix + dst_path)
                except EnvironmentError:
                    failed_paths.append(src_path)
            if failed_paths:
                raise Error(
                    'Failed to %s the entries "%s".'
                    % ('move' if action == 'mv' else 'copy',
                       '", "'.join(failed_paths)))
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


def _make_git_runner(request, app_name):
    author_name, author_email = (
        (request.user.username, request.user.email)
        if request.user.is_authenticated() else
        ('anonym', ''))
    return GitRunner(request.dev_name, app_name, author_name, author_email)


class GitHandler(BaseHandler):
    allowed_methods = ('POST',)

    @_getting_app_path
    def post(self, request, app_name, app_path):
        command, args = parse_git_command(request.data['command'])
        host_id = get_id(request.dev_name, app_name)
        if command in ('commit', 'merge', 'pull', 'rebase', 'reset', 'revert'):
            _purge_domains(json.loads(read_file(app_path.domains)))
        else:
            host_id += ':'
        stop_patsaks(host_id)
        return HttpResponse(
            _make_git_runner(request, app_name).run(command, *args),
            'text/plain; charset=utf-8')


class DiffHandler(BaseHandler):
    allowed_methods = ('GET',)

    @_getting_app_path
    def get(self, request, app_name, app_path):
        if request.is_anonymous:
            return HttpResponse('', 'text/plain; charset=utf-8')
        git_runner = _make_git_runner(request, app_name)
        parts = [git_runner.run('diff', 'HEAD')]
        for status_line in git_runner.run(
            'status', '--porcelain', '--untracked-files=all').splitlines():
            if not status_line.startswith('?? '):
                continue
            escaped = status_line[3] == '"'
            path = status_line[4:-1] if escaped else status_line[3:]
            content = read_file(
                app_path.code + '/' +
                (path.decode('string_escape') if escaped else path))
            a_path = '"a/%s"' % path if escaped else 'a/' + path
            b_path = '"b/%s"' % path if escaped else 'b/' + path
            parts.append('diff --git %s %s\n' % (a_path, b_path))
            if content:
                parts.append('added new file\n--- /dev/null\n+++ %s\n' % b_path)
                if '\0' in content:
                    parts.append(
                        'Binary files /dev/null and %s differ\n' % b_path)
                else:
                    parts += ['+%s\n' % line for line in content.splitlines()]
                    if content[-1] != '\n':
                        parts.append('\\ No newline at end of file\n')
            else:
                parts.append('added new empty file\n')
        return HttpResponse(''.join(parts), 'text/plain; charset=utf-8')


class CommitHandler(BaseHandler):
    allowed_methods = ('POST',)

    @_getting_app_path
    def post(self, request, app_name, app_path):
        _purge_domains(json.loads(read_file(app_path.domains)))
        stop_patsaks(get_id(request.dev_name, app_name))
        git_runner = _make_git_runner(request, app_name)
        git_runner.run('add', '-A')
        args = ['commit', '-qm', request.data['message']]
        if request.data.get('amend'):
            args.append('--amend')
        output = git_runner.run(*args)
        if output:
            raise Error(output)
        return HttpResponse()


class PublicHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT')
    access = AUTHENTICATED

    @_getting_app_path
    def get(self, request, app_name, app_path):
        return os.path.exists(ROOT.devs[request.dev_name].libs[app_name])

    @_getting_app_path
    def put(self, request, app_name, app_path):
        lib_path = ROOT.devs[request.dev_name].libs[app_name]
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
        return HttpResponse()
