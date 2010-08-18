# (c) 2010 by Anton Korenyushkin

import os.path
import os

from settings import DEBUG
from utils import write_file


ANONYM_PREFIX = 'anonym'
ANONYM_NAME = ANONYM_PREFIX
SAMPLE_NAME = 'hello-world'


def setup_paths(root_path):
    global ROOT_PATH, LOCKS_PATH
    global DRAFTS_PATH, CURR_DRAFT_PATH, NEXT_DRAFT_PATH
    global DATA_PATH, DEVS_PATH, DOMAINS_PATH
    ROOT_PATH = root_path
    LOCKS_PATH = ROOT_PATH + '/locks'
    DRAFTS_PATH = ROOT_PATH + '/drafts'
    CURR_DRAFT_PATH = DRAFTS_PATH + '/curr'
    NEXT_DRAFT_PATH = DRAFTS_PATH + '/next'
    DATA_PATH = ROOT_PATH + '/data'
    DEVS_PATH = DATA_PATH + '/devs'
    DOMAINS_PATH = DATA_PATH + '/domains'


setup_paths(
    os.path.abspath(os.path.dirname(__file__)) + '/root' if DEBUG else '/ak')


def get_lock_path(dev_name):
    return LOCKS_PATH + '/' + dev_name


def get_dev_path(dev_name):
    return DEVS_PATH + '/' + dev_name


def create_dev(dev_name=None):
    draft_name = os.readlink(CURR_DRAFT_PATH)
    os.symlink(str(int(draft_name) + 1), NEXT_DRAFT_PATH)
    os.rename(NEXT_DRAFT_PATH, CURR_DRAFT_PATH)
    dev_name = dev_name or ANONYM_PREFIX + draft_name
    os.rename(DRAFTS_PATH + '/' + draft_name, get_dev_path(dev_name))
    open(get_lock_path(dev_name), 'w').close()
    return dev_name


def get_config_path(dev_name):
    return get_dev_path(dev_name) + '/config'


def get_apps_path(dev_name):
    return get_dev_path(dev_name) + '/apps'


def get_app_path(dev_name, app_name):
    return get_apps_path(dev_name) + '/' + app_name


def get_code_path(dev_name, app_name):
    return get_app_path(dev_name, app_name) + '/code'


def create_paths():
    for path in (
        ROOT_PATH,
        LOCKS_PATH,
        DRAFTS_PATH,
        DATA_PATH,
        DEVS_PATH,
        DOMAINS_PATH,
        get_dev_path(ANONYM_NAME),
        get_apps_path(ANONYM_NAME),
        get_app_path(ANONYM_NAME, SAMPLE_NAME),
    ):
        if not os.path.isdir(path):
            os.mkdir(path)
    anonym_config_path = get_config_path(ANONYM_NAME)
    if not os.path.isfile(anonym_config_path):
        write_file(anonym_config_path, '{}')
    anonym_code_path = get_code_path(ANONYM_NAME, SAMPLE_NAME)
    if not os.path.islink(anonym_code_path):
        os.symlink(os.path.abspath(os.path.dirname(__file__) + '/sample'),
                   anonym_code_path)
