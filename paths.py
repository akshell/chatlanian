# (c) 2010 by Anton Korenyushkin

import os.path
import os

from settings import DEBUG
from utils import write_file


ANONYM_PREFIX = 'anonym'
ANONYM_NAME = ANONYM_PREFIX
SAMPLE_NAME = 'hello-world'
SAMPLE_PATH = os.path.abspath(os.path.dirname(__file__)) + '/sample'


class Path(str):
    child_class = str

    def __getitem__(self, name):
        return self.child_class(self + '/' + name.lower())


def _child(name, cls=str):
    suffix = '/' + name
    @property
    def result(self):
        return cls(self + suffix)
    return result


class DraftsPath(Path):
    curr = _child('curr')
    next = _child('next')


class AppPath(Path):
    name = _child('name')
    code = _child('code')
    git = _child('git')
    domains = _child('domains', Path)
    envs = _child('envs', Path)


class AppsPath(Path):
    child_class = AppPath


class DevPath(Path):
    config = _child('config')
    rsa_pub = _child('rsa.pub')
    apps = _child('apps', AppsPath)


class DevsPath(Path):
    child_class = DevPath


def setup_paths(root_path):
    global LOCKS_PATH, DRAFTS_PATH, DEVS_PATH, DOMAINS_PATH
    LOCKS_PATH = Path(root_path + '/locks')
    DRAFTS_PATH = DraftsPath(root_path + '/drafts')
    DEVS_PATH = DevsPath(root_path + '/data/devs')
    DOMAINS_PATH = Path(root_path + '/data/domains')


setup_paths(
    os.path.abspath(os.path.dirname(__file__)) + '/root' if DEBUG else '/ak')


def create_paths():
    dev_path = DEVS_PATH[ANONYM_NAME]
    app_path = dev_path.apps[SAMPLE_NAME]
    for path in (
        LOCKS_PATH,
        DRAFTS_PATH,
        DOMAINS_PATH,
        app_path,
    ):
        if not os.path.isdir(path):
            os.makedirs(path)
    if not os.path.isfile(dev_path.config):
        write_file(dev_path.config, '{}')
    if not os.path.isfile(app_path.name):
        write_file(app_path.name, SAMPLE_NAME)
    if not os.path.islink(app_path.code):
        os.symlink(SAMPLE_PATH, app_path.code)
