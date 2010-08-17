# (c) 2010 by Anton Korenyushkin

import httplib
import os

from piston.handler import AnonymousBaseHandler, BaseHandler
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib import auth
from django.http import HttpResponse

from error import Error
from utils import check_name
from paths import get_lock_path, get_dev_path


class AnonymousSignupHandler(AnonymousBaseHandler):
    allowed_methods = ('POST',)

    def create(self, request):
        name = request.data['name']
        check_name(name)
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
        open(get_lock_path(name), 'w').close()
        os.mkdir(get_dev_path(name))
        user.backend = 'chatlanian.auth_backend.AuthBackend'
        auth.login(request, user)
        return HttpResponse(status=httplib.CREATED)


class SignupHandler(BaseHandler):
    anonymous = AnonymousSignupHandler
    allowed_methods = ()


class AnonymousLoginHandler(AnonymousBaseHandler):
    allowed_methods = ('POST',)

    def create(self, request):
        user = auth.authenticate(
            username=request.data['name'].replace(' ', '-'),
            password=request.data['password'])
        if not user or not user.is_active:
            raise Error('Bad user name or password')
        auth.login(request, user)
        return HttpResponse()


class LoginHandler(BaseHandler):
    anonymous = AnonymousLoginHandler
    allowed_methods = ()


class LogoutHandler(BaseHandler):
    allowed_methods = ('POST',)

    def create(self, request):
        auth.logout(request)
        return HttpResponse()
