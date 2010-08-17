# (c) 2010 by Anton Korenyushkin

import os.path
import os

from settings import DEBUG


def setup_paths(root_path, create=False):
    global ROOT_PATH, LOCKS_PATH, DATA_PATH, DEVS_PATH, DOMAINS_PATH
    ROOT_PATH = root_path
    LOCKS_PATH = ROOT_PATH + 'locks/'
    DATA_PATH = ROOT_PATH + 'data/'
    DEVS_PATH = DATA_PATH + 'devs/'
    DOMAINS_PATH = DATA_PATH + 'domains/'
    if create:
        for path in (
            ROOT_PATH,
            LOCKS_PATH,
            DATA_PATH,
            DEVS_PATH,
            DOMAINS_PATH,
        ):
            if not os.path.isdir(path):
                os.mkdir(path)


setup_paths(
    os.path.abspath(os.path.dirname(__file__)) + '/root/' if DEBUG else '/ak/',
    DEBUG)


def get_lock_path(dev_name):
    return LOCKS_PATH + dev_name


def get_dev_path(dev_name):
    return DEVS_PATH + dev_name
