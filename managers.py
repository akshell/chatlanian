# (c) 2010 by Anton Korenyushkin

import os
import os.path
import shutil

from django.db import connection, transaction

from error import Error
from utils import read_file, write_file, touch_file, get_schema_name
from paths import (
    ANONYM_PREFIX, SAMPLE_NAME, SAMPLE_PATH, LOCKS_PATH, DRAFTS_PATH, DEVS_PATH)
from git import run_git


CREATE_SCHEMA_SQL = 'SELECT ak.create_schema(%s);'


@transaction.commit_manually
def create_app(dev_name, app_name):
    app_path = DEVS_PATH[dev_name].apps[app_name]
    if os.path.isdir(app_path):
        raise Error(
            'The app "%s" already exists.' % read_file(app_path.name),
            'App name must be case-insensitively unique.')
    main_schema_name = get_schema_name(dev_name, app_name)
    connection.cursor().execute(
        CREATE_SCHEMA_SQL * 2, (main_schema_name, main_schema_name + ':debug'))
    transaction.commit()
    os.mkdir(app_path)
    write_file(app_path.name, app_name)
    shutil.copytree(SAMPLE_PATH, app_path.code)
    os.mkdir(app_path.git)
    os.mkdir(app_path.envs)
    write_file(app_path.envs['debug'], 'debug')
    write_file(app_path.domains, '[]')
    run_git(dev_name, app_name, 'init', '--quiet')
    run_git(dev_name, app_name, 'add', '.')
    run_git(
        dev_name, app_name,
        'commit', '--quiet',
        '--author', 'akshell <akshell@akshell.com>',
        '--message', 'Initial commit.')


def create_dev(dev_name=None):
    draft_name = os.readlink(DRAFTS_PATH.curr)
    os.symlink(str(int(draft_name) + 1), DRAFTS_PATH.next)
    os.rename(DRAFTS_PATH.next, DRAFTS_PATH.curr)
    dev_name = dev_name or ANONYM_PREFIX + draft_name
    dev_path = DEVS_PATH[dev_name]
    os.rename(DRAFTS_PATH[draft_name], dev_path)
    write_file(dev_path.ssh, '''\
#!/bin/bash
exec /usr/bin/ssh -i "%s" "$@"
''' % dev_path.rsa)
    os.chmod(dev_path.ssh, 0544)
    create_app(dev_name, SAMPLE_NAME)
    touch_file(LOCKS_PATH[dev_name])
    return dev_name
