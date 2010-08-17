#!/usr/bin/env python

# (c) 2010 by Anton Korenyushkin

# pylint: disable-msg=W0404

import os.path
import os
import sys

from coverage import coverage
from django.core.management import setup_environ


PACKAGE_DIR = os.path.dirname(__file__)
COV_DIR = PACKAGE_DIR + '/cov'


def main():
    cov = coverage()
    cov.start()
    import settings
    setup_environ(settings)
    from django.conf import settings
    from django.test.utils import get_runner
    test_runner = get_runner(settings)()
    failures = test_runner.run_tests(('chatlanian',))
    cov.stop()
    modules = [
        __import__(name[:-3])
        for name in os.listdir(PACKAGE_DIR)
        if name.endswith('.py') and name != 'cov.py' and name != 'manage.py'
    ]
    cov.report(modules)
    cov.html_report(modules, directory=COV_DIR)
    sys.exit(bool(failures))


if __name__ == '__main__':
    main()
