# (c) 2010 by Anton Korenyushkin

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
