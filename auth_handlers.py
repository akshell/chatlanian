# (c) 2010 by Anton Korenyushkin

from __future__ import with_statement
import httplib
import os
import subprocess
import tempfile

from piston.handler import AnonymousBaseHandler, BaseHandler
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib import auth
from django.http import HttpResponse

from error import Error
from utils import check_name
from paths import TMP_PATH, get_lock_path, get_dev_path


_draft_path = None
_keygen_process = None


def _prepare_draft():
    global _draft_path, _keygen_process
    _draft_path = tempfile.mkdtemp(prefix='draft-', dir=TMP_PATH)
    with open(_draft_path + '/config', 'w') as f:
        f.write('{}')
    _keygen_process = subprocess.Popen(
        ['ssh-keygen', '-q', '-N', '', '-C', '', '-f', _draft_path + '/rsa'])


_prepare_draft()


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
        _keygen_process.wait()
        os.rename(_draft_path, get_dev_path(name))
        _prepare_draft()
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
