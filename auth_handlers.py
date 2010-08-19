# (c) 2010 by Anton Korenyushkin

import httplib
import os
import shutil

from piston.handler import BaseHandler
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib import auth
from django.http import HttpResponse

from error import Error
from utils import check_name
from paths import ANONYM_PREFIX, locks_path, devs_path, create_dev


class SignupHandler(BaseHandler):
    allowed_methods = ('POST',)
    handles_anonyms = True

    def create(self, request):
        name = request.data['name']
        check_name(name)
        if name.startswith(ANONYM_PREFIX):
            raise Error(
                'Names starting with "%s" are reserved.' % ANONYM_PREFIX,
                'Please choose another name.')
        try:
            user = User.objects.get(username__iexact=name)
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
        user = User.objects.create_user(name, email, request.data['password'])
        user.save()
        if request.is_half_anonymous:
            open(locks_path[name], 'w').close()
            os.rename(devs_path[request.dev_name], devs_path[name])
            os.remove(locks_path[request.dev_name])
        else:
            create_dev(name)
        user.backend = 'chatlanian.auth_backend.AuthBackend'
        auth.login(request, user)
        return HttpResponse(status=httplib.CREATED)


class LoginHandler(BaseHandler):
    allowed_methods = ('POST',)
    handles_anonyms = True

    def create(self, request):
        user = auth.authenticate(
            username=request.data['name'].replace(' ', '-'),
            password=request.data['password'])
        if not user or not user.is_active:
            raise Error('Bad user name or password')
        auth.login(request, user)
        if request.is_half_anonymous:
            shutil.rmtree(devs_path[request.dev_name])
            os.remove(locks_path[request.dev_name])
        return HttpResponse()


class LogoutHandler(BaseHandler):
    allowed_methods = ('POST',)
    handles_anonyms = True

    def create(self, request):
        auth.logout(request)
        return HttpResponse()
