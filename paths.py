# (c) 2010 by Anton Korenyushkin

import os.path
import os

from settings import DEBUG
from utils import write_file, touch_file, SharedLock, ExclusiveLock


ANONYM_PREFIX = 'anonym'
ANONYM_NAME = ANONYM_PREFIX
SAMPLE_NAME = 'hello-world'
CHATLANIAN_PATH = os.path.abspath(os.path.dirname(__file__))
SAMPLE_PATH = CHATLANIAN_PATH + '/sample'
PATSAK_INIT_SQL_PATH = os.path.dirname(CHATLANIAN_PATH) + '/patsak/init.sql'
CHATLANIAN_INIT_SQL_PATH = CHATLANIAN_PATH + '/init.sql'


class DirPath(str):
    child_class = str

    def __getitem__(self, name):
        return self.child_class(self + '/' + name.lower())


def _child(name, cls=str):
    suffix = '/' + name
    @property
    def result(self):
        return cls(self + suffix)
    return result


class LockPath(str):
    def acquire_shared(self):
        return SharedLock(self)

    def acquire_exclusive(self):
        return ExclusiveLock(self)


class LocksPath(DirPath):
    child_class = LockPath
    domains = _child('!domains', LockPath)


class DraftsPath(DirPath):
    curr = _child('curr')
    next = _child('next')


class AppPath(DirPath):
    name = _child('name')
    code = _child('code')
    git = _child('git')
    domains = _child('domains', DirPath)
    envs = _child('envs', DirPath)


class AppsPath(DirPath):
    child_class = AppPath


class DevPath(DirPath):
    config = _child('config')
    rsa_pub = _child('rsa.pub')
    apps = _child('apps', AppsPath)


class DevsPath(DirPath):
    child_class = DevPath


def setup_paths(root_path):
    global LOCKS_PATH, DRAFTS_PATH, TMP_PATH, DEVS_PATH, DOMAINS_PATH
    LOCKS_PATH = LocksPath(root_path + '/locks')
    DRAFTS_PATH = DraftsPath(root_path + '/drafts')
    TMP_PATH = DirPath(root_path + '/tmp')
    DEVS_PATH = DevsPath(root_path + '/data/devs')
    DOMAINS_PATH = DirPath(root_path + '/data/domains')


setup_paths(
    os.path.abspath(os.path.dirname(__file__)) + '/root' if DEBUG else '/ak')


def create_paths():
    dev_path = DEVS_PATH[ANONYM_NAME]
    app_path = dev_path.apps[SAMPLE_NAME]
    for path in (
        LOCKS_PATH,
        DRAFTS_PATH,
        TMP_PATH,
        DOMAINS_PATH,
        app_path,
    ):
        if not os.path.isdir(path):
            os.makedirs(path)
    touch_file(LOCKS_PATH.domains)
    write_file(dev_path.config, '{}')
    write_file(app_path.name, SAMPLE_NAME)
    if not os.path.islink(app_path.code):
        os.symlink(SAMPLE_PATH, app_path.code)
