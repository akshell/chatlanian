# (c) 2010 by Anton Korenyushkin

import socket


DEBUG = 'akshell' not in socket.gethostname()
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Anton Korenyushkin', 'anton@akshell.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'chatlanian',
        'TEST_NAME': 'test-chatlanian',
    }
}

TIME_ZONE = 'UTC'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = False

USE_L10N = False

ADMIN_MEDIA_PREFIX = '/admin/media/'

SECRET_KEY = 'm&ccq7#3m#%pfud^@&q_zal=5*lj#%6fu-h%@=bjwm(ondy5y('

TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'chatlanian.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'chatlanian',
)

AUTHENTICATION_BACKENDS = (
    'chatlanian.auth_backend.AuthBackend',
)
