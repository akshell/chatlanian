# (c) 2010-2011 by Anton Korenyushkin

from __future__ import with_statement
import re
import fcntl

from django.db import connection

from error import Error


NAME_RE = re.compile('^%(w)s(?:%(w)s|-%(w)s)*$' % {'w': '[a-zA-Z0-9]'})
MAX_NAME_LEN = 30
NAME_PATTERN = '[a-zA-Z0-9-]{1,%d}' % MAX_NAME_LEN


def check_name(name):
    if not NAME_RE.match(name):
        raise Error(
            'The name "%s" is incorrect.' % name,
            ('Name must consist of Latin letters, digits, and single hyphens.' +
             'It must not start or end with a hyphen.'))
    if len(name) > MAX_NAME_LEN:
        raise Error(
            'The name is too long.',
            'Name length must not exceed %d characters.' % MAX_NAME_LEN)


def read_file(path):
    with open(path) as f:
        return f.read()


def write_file(path, data):
    with open(path, 'w') as f:
        f.write(data)


def touch_file(path):
    open(path, 'w').close()


def get_id(dev_name, app_name, env_name=None):
    result = dev_name + ':' + app_name
    if env_name:
        result += ':' + env_name
    return result.lower()


def execute_sql(query, params=()):
    connection.cursor().execute(query, params)


class BaseLock(object):
    def __init__(self, path):
        self._file = open(path)
        fcntl.flock(self._file, self.kind)

    def release(self):
        self._file.close()

    def __enter__(self):
        pass

    def __exit__(self, cls, value, traceback):
        self.release()


class SharedLock(BaseLock):
    kind = fcntl.LOCK_SH


class ExclusiveLock(BaseLock):
    kind = fcntl.LOCK_EX
