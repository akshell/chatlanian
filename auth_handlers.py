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
from paths import ANONYM_PREFIX, ROOT
from managers import create_dev, stop_patsaks
from resource import ANONYMOUS, AUTHENTICATED


class SignupHandler(BaseHandler):
    allowed_methods = ('POST',)
    access = ANONYMOUS

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
            raise Error('The email "%s" is incorrect.' % email,
                        'Please correct the email.')
        if User.objects.filter(email=email):
            raise Error(
                'The email "%s" has already been taken.' % email,
                'Please choose another email.')
        user = User.objects.create_user(
            dev_name, email, request.data['password'])
        user.save()
        if request.is_half_anonymous:
            old_dev_path = ROOT.devs[request.dev_name]
            for app_name in os.listdir(old_dev_path.apps):
                stop_patsaks(get_id(request.dev_name, app_name))
            dev_path = ROOT.devs[dev_name]
            os.rename(old_dev_path, dev_path)
            os.rename(
                dev_path.grantors[request.dev_name],
                dev_path.grantors[dev_name])
            os.rename(ROOT.locks[request.dev_name], ROOT.locks[dev_name])
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
    access = ANONYMOUS

    def post(self, request):
        user = auth.authenticate(
            username=request.data['name'].replace(' ', '-'),
            password=request.data['password'])
        if not user or not user.is_active:
            raise Error('Incorrect user name or password.')
        if request.is_half_anonymous:
            execute_sql('SELECT ak.drop_schemas(%s)', (request.dev_name,))
            execute_sql('DROP TABLESPACE "%s"' % request.dev_name)
            os.rename(ROOT.devs[request.dev_name], ROOT.trash[request.dev_name])
            os.remove(ROOT.locks[request.dev_name])
        auth.login(request, user)
        return HttpResponse()


class LogoutHandler(BaseHandler):
    allowed_methods = ('POST',)
    access = AUTHENTICATED

    def post(self, request):
        auth.logout(request)
        return HttpResponse()


class PasswordHandler(BaseHandler):
    allowed_methods = ('POST',)
    access = AUTHENTICATED

    def post(self, request):
        if not request.user.check_password(request.data['old']):
            raise Error('The old password is incorrect.',
                        'Please retype the old password.')
        request.user.set_password(request.data['new'])
        request.user.save()
        return HttpResponse()
