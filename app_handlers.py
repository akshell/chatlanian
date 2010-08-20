# (c) 2010 by Anton Korenyushkin

from __future__ import with_statement
import re
import os
import shutil
import httplib

import simplejson as json
from piston.handler import BaseHandler
from piston.utils import require_mime
from django.http import HttpResponse
from django.db import connection, transaction

from error import Error
from utils import check_name, read_file, write_file, get_schema_name
from paths import LOCKS_PATH, TMP_PATH, DEVS_PATH, DOMAINS_PATH
from managers import CREATE_SCHEMA_SQL


def _getting_app_path(func):
    def result(self, request, app_name, **kwargs):
        app_path = DEVS_PATH[request.dev_name].apps[app_name]
        if not os.path.exists(app_path):
            raise Error(
                'The app "%s" does not exist.' % app_name,
                status=httplib.NOT_FOUND)
        return func(self, request, app_name, app_path=app_path, **kwargs)
    return result


class AppHandler(BaseHandler):
    allowed_methods = ('DELETE')

    @_getting_app_path
    def delete(self, request, app_name, app_path):
        schema_name = get_schema_name(request.dev_name, app_name)
        tmp_app_path = TMP_PATH[schema_name]
        os.rename(app_path, tmp_app_path)
        shutil.rmtree(tmp_app_path)
        connection.cursor().execute(
            'SELECT ak.drop_schemas(%s)', (schema_name,))


def _check_env_does_not_exist(env_path):
    if os.path.exists(env_path):
        raise Error(
            'The environment "%s" already exists.' % read_file(env_path),
            'Environment name must be case-insensitively unique.')


class EnvsHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')

    @_getting_app_path
    def get(self, request, app_name, app_path):
        return [
            read_file(app_path.envs[lower_name])
            for lower_name in sorted(os.listdir(app_path.envs))
        ]

    @transaction.commit_manually
    @_getting_app_path
    def post(self, request, app_name, app_path):
        env_name = request.data['name']
        check_name(env_name)
        env_path = app_path.envs[env_name]
        _check_env_does_not_exist(env_path)
        connection.cursor().execute(
            CREATE_SCHEMA_SQL,
            (get_schema_name(request.dev_name, app_name, env_name),))
        transaction.commit()
        write_file(env_path, env_name)
        return HttpResponse(status=httplib.CREATED)


def _check_env_exists(env_name, env_path):
    if not os.path.exists(env_path):
        raise Error(
            'The environment "%s" does not exist.' % env_name,
            status=httplib.NOT_FOUND)


class EnvHandler(BaseHandler):
    allowed_methods = ('POST', 'DELETE')

    @transaction.commit_manually
    @_getting_app_path
    def post(self, request, app_name, env_name, app_path):
        env_path = app_path.envs[env_name]
        _check_env_exists(env_name, env_path)
        new_env_name = request.data['name']
        check_name(new_env_name)
        new_env_path = app_path.envs[new_env_name]
        _check_env_does_not_exist(new_env_path)
        write_file(new_env_path, new_env_name)
        schema_prefix = get_schema_name(request.dev_name, app_name) + ':'
        connection.cursor().execute(
            'ALTER SCHEMA "%s" RENAME TO "%s"'
            % (schema_prefix + env_name.lower(),
               schema_prefix + new_env_name.lower()))
        transaction.commit()
        os.remove(env_path)
        return HttpResponse()

    @_getting_app_path
    def delete(self, request, app_name, env_name, app_path):
        env_path = app_path.envs[env_name]
        _check_env_exists(env_name, env_path)
        os.remove(env_path)
        connection.cursor().execute(
            'DROP SCHEMA "%s" CASCADE'
            % get_schema_name(request.dev_name, app_name, env_name))
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
            schema_name = get_schema_name(request.dev_name, app_name)
            for new_domain_lower in new_domains_lower.difference(domains_lower):
                write_file(DOMAINS_PATH[new_domain_lower], schema_name)
            for old_domain_lower in domains_lower.difference(new_domains_lower):
                os.remove(DOMAINS_PATH[old_domain_lower])
        write_file(app_path.domains, json.dumps(new_domains))
        return HttpResponse()
