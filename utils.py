# (c) 2010 by Anton Korenyushkin

from __future__ import with_statement
import re

from error import Error


NAME_RE = re.compile('^%(w)s(?:%(w)s|-%(w)s)*$' % {'w': '[a-zA-Z0-9]'})
MAX_NAME_LEN = 30


def check_name(name):
    if not NAME_RE.match(name):
        raise Error(
            'The name "%s" is incorrect.' % name,
            ('Name must consist of Latin letters, digits, and single hyphens.' +
             'It must not start or end with a hyphen.'))
    if len(name) > MAX_NAME_LEN:
        raise Error(
            'The name is too long.',
            'Name length must not exceed %d characters.')


def read_file(path):
    with open(path) as f:
        return f.read()


def write_file(path, data):
    with open(path, 'w') as f:
        f.write(data)


def get_schema_name(dev_name, app_name, env_name=None):
    schema_name = dev_name + ':' + app_name
    if env_name:
        schema_name += ':' + env_name
    return schema_name.lower()
