# (c) 2010 by Anton Korenyushkin

from __future__ import with_statement
from httplib import CREATED
import os

from piston.handler import BaseHandler
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib import auth
from django.http import HttpResponse

from error import Error
from utils import check_name, get_id, execute_sql
from paths import ANONYM_PREFIX, LOCKS_PATH, DEVS_PATH
from managers import create_dev, stop_patsaks


class SignupHandler(BaseHandler):
    allowed_methods = ('POST',)
    handles_anonyms = True

    def post(self, request):
        dev_name = request.data['name']
        check_name(dev_name)
        if dev_name.startswith(ANONYM_PREFIX):
            raise Error(
                'Names starting with "%s" are reserved.' % ANONYM_PREFIX,
                'Please choose another name.')
        try:
            user = User.objects.get(username__iexact=dev_name)
        except User.DoesNotExist:
            pass
        else:
            raise Error(
                'The user "%s" already exists.' % user.username,
                'Name must be be case-insensitively unique.')
        email = request.data['email']
        try:
            validate_email(email)
        except ValidationError:
            raise Error('The email "%s" is incorrect.' % email)
        if User.objects.filter(email=email):
            raise Error(
                'The email "%s" has already been taken.' % email,
                'Please choose another email.')
        user = User.objects.create_user(
            dev_name, email, request.data['password'])
        user.save()
        if request.is_half_anonymous:
            old_dev_path = DEVS_PATH[request.dev_name]
            for app_name in os.listdir(old_dev_path.apps):
                stop_patsaks(get_id(request.dev_name, app_name))
            dev_path = DEVS_PATH[dev_name]
            os.rename(old_dev_path, dev_path)
            os.rename(
                dev_path.grantors[request.dev_name],
                dev_path.grantors[dev_name])
            os.rename(LOCKS_PATH[request.dev_name], LOCKS_PATH[dev_name])
            execute_sql('''\
UPDATE pg_tablespace SET spclocation = %s, spcname = %s WHERE spcname = %s''',
                        (dev_path.tablespace,
                         dev_name.lower(),
                         request.dev_name))
        else:
            create_dev(dev_name)
        user.backend = 'chatlanian.auth_backend.AuthBackend'
        auth.login(request, user)
        return HttpResponse(status=CREATED)


class LoginHandler(BaseHandler):
    allowed_methods = ('POST',)
    handles_anonyms = True

    def post(self, request):
        user = auth.authenticate(
            username=request.data['name'].replace(' ', '-'),
            password=request.data['password'])
        if not user or not user.is_active:
            raise Error('Bad user name or password')
        auth.login(request, user)
        return HttpResponse()


class LogoutHandler(BaseHandler):
    allowed_methods = ('POST',)
    handles_anonyms = True

    def post(self, request):
        auth.logout(request)
        return HttpResponse()
