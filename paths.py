# (c) 2010 by Anton Korenyushkin

import os.path
import os

from settings import DEBUG, DATABASES
from utils import write_file, touch_file, SharedLock, ExclusiveLock


ANONYM_PREFIX = 'anonym'
ANONYM_NAME = ANONYM_PREFIX
SAMPLE_NAME = 'hello-world'
INITIAL_ENV_NAME = 'debug'
CHATLANIAN_PATH = os.path.abspath(os.path.dirname(__file__))
SAMPLE_PATH = CHATLANIAN_PATH + '/sample'
CHATLANIAN_INIT_SQL_PATH = CHATLANIAN_PATH + '/init.sql'
PATSAK_PATH = os.path.dirname(CHATLANIAN_PATH) + '/patsak'
PATSAK_INIT_SQL_PATH = PATSAK_PATH + '/init.sql'
PATSAK_EXE_PATH = PATSAK_PATH + '/exe/common/patsak'
ECILOP_PATH = os.path.dirname(CHATLANIAN_PATH) + '/ecilop'
ECILOP_EXE_PATH = ECILOP_PATH + '/ecilop'


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


class AppPath(str):
    name = _child('name')
    code = _child('code')
    git = _child('git')
    domains = _child('domains', DirPath)
    envs = _child('envs', DirPath)


class AppsPath(DirPath):
    child_class = AppPath


class DevPath(str):
    tablespace = _child('tablespace')
    config = _child('config')
    rsa_pub = _child('rsa.pub')
    ssh = _child('ssh')
    apps = _child('apps', AppsPath)
    libs = _child('libs', AppsPath)
    grantors = _child('grantors', DirPath)


class DevsPath(DirPath):
    child_class = DevPath


class DraftsPath(DirPath):
    child_class = DevPath
    curr = _child('curr', DevPath)
    next = _child('next', DevPath)


class RootPath(str):
    locks = _child('locks', LocksPath)
    drafts = _child('drafts', DraftsPath)
    tmp = _child('tmp', DirPath)
    trash = _child('trash', DirPath)
    ecilop_socket = _child('ecilop.socket')
    data = _child('data')
    devs = _child('data/devs', DevsPath)
    domains = _child('data/domains', DirPath)
    patsak_conf = _child('patsak.conf')
    ecilop_conf = _child('ecilop.conf')


ROOT = RootPath(
    os.path.abspath(os.path.dirname(__file__)) + '/root' if DEBUG else '/ak')


def create_paths(use_test_db=False):
    dev_path = ROOT.devs[ANONYM_NAME]
    app_path = dev_path.apps[SAMPLE_NAME]
    for path in (
        ROOT.locks,
        ROOT.drafts,
        ROOT.tmp,
        ROOT.trash,
        ROOT.domains,
        app_path,
    ):
        if not os.path.isdir(path):
            os.makedirs(path)
    touch_file(ROOT.locks.domains)
    write_file(dev_path.config, '{}')
    write_file(app_path.name, SAMPLE_NAME)
    if not os.path.islink(app_path.code):
        os.symlink(SAMPLE_PATH, app_path.code)
    if not os.path.isdir(app_path.envs):
        os.mkdir(app_path.envs)
        write_file(app_path.envs[INITIAL_ENV_NAME], INITIAL_ENV_NAME)
    write_file(ROOT.patsak_conf, '''\
lib=%s/lib
db=dbname=%s
''' % (PATSAK_PATH,
       DATABASES['default']['TEST_NAME' if use_test_db else 'NAME']))
    write_file(ROOT.ecilop_conf, '''\
socket=%s
data=%s
locks=%s
patsak=%s
patsak-config=%s
''' % (ROOT.ecilop_socket, ROOT.data, ROOT.locks,
       PATSAK_EXE_PATH, ROOT.patsak_conf))
