# (c) 2010 by Anton Korenyushkin

from subprocess import Popen
import os
import os.path
import shutil

from error import Error
from utils import read_file, write_file
from paths import (
    SAMPLE_PATH, ANONYM_PREFIX, SAMPLE_NAME, LOCKS_PATH, DRAFTS_PATH, DEVS_PATH)


def create_app(dev_name, app_name):
    app_path = DEVS_PATH[dev_name].apps[app_name]
    if os.path.isdir(app_path):
        raise Error(
            'The app "%s" already exists.' % read_file(app_path.name),
            'App name must be case-insensitively unique.')
    os.mkdir(app_path)
    write_file(app_path.name, app_name)
    shutil.copytree(SAMPLE_PATH, app_path.code)
    os.mkdir(app_path.git)
    os.mkdir(app_path.domains)
    os.mkdir(app_path.envs)
    write_file(app_path.envs['debug'], 'debug')
    cmd = ['git', '--work-tree', app_path.code, '--git-dir', app_path.git]
    Popen(cmd + ['init', '--quiet']).wait()
    Popen(cmd + ['add', '.']).wait()
    Popen(
        cmd + [
            'commit', '--quiet',
            '--author', 'akshell <akshell@akshell.com>',
            '--message', 'Initial commit.',
        ]).wait()


def create_dev(dev_name=None):
    draft_name = os.readlink(DRAFTS_PATH.curr)
    os.symlink(str(int(draft_name) + 1), DRAFTS_PATH.next)
    os.rename(DRAFTS_PATH.next, DRAFTS_PATH.curr)
    dev_name = dev_name or ANONYM_PREFIX + draft_name
    os.rename(DRAFTS_PATH[draft_name], DEVS_PATH[dev_name])
    create_app(dev_name, SAMPLE_NAME)
    open(LOCKS_PATH[dev_name], 'w').close()
    return dev_name
