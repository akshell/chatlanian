# From http://blog.shopfiber.com/case-insensitive-username-login-in-django/

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class AuthBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username__iexact=username)
            if user.check_password(password):
                return user
            else:
                return None
        except User.DoesNotExist:
            return None
