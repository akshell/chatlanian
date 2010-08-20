# (c) 2010 by Anton Korenyushkin

import os
import shutil
import httplib

from piston.handler import BaseHandler
from django.http import HttpResponse
from django.db import connection, transaction

from error import Error
from utils import check_name, read_file, write_file, get_schema_name
from paths import TMP_PATH, DEVS_PATH
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
    def read(self, request, app_name, app_path):
        return [
            read_file(app_path.envs[lower_name])
            for lower_name in sorted(os.listdir(app_path.envs))
        ]

    @transaction.commit_manually
    @_getting_app_path
    def create(self, request, app_name, app_path):
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
    def create(self, request, app_name, env_name, app_path):
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
