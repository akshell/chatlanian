# (c) 2010 by Anton Korenyushkin

from subprocess import Popen
import os.path
import os
import shutil

from settings import DEBUG
from error import Error
from utils import read_file, write_file


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
    global ROOT_PATH, LOCKS_PATH
    global DRAFTS_PATH, CURR_DRAFT_PATH, NEXT_DRAFT_PATH
    global DATA_PATH, DEVS_PATH, DOMAINS_PATH
    global locks_path, devs_path, domains_path
    ROOT_PATH = root_path
    LOCKS_PATH = ROOT_PATH + '/locks'
    DRAFTS_PATH = ROOT_PATH + '/drafts'
    CURR_DRAFT_PATH = DRAFTS_PATH + '/curr'
    NEXT_DRAFT_PATH = DRAFTS_PATH + '/next'
    DATA_PATH = ROOT_PATH + '/data'
    DEVS_PATH = DATA_PATH + '/devs'
    DOMAINS_PATH = DATA_PATH + '/domains'
    locks_path = Path(LOCKS_PATH)
    devs_path = DevsPath(DEVS_PATH)
    domains_path = Path(DOMAINS_PATH)


setup_paths(
    os.path.abspath(os.path.dirname(__file__)) + '/root' if DEBUG else '/ak')


def create_paths():
    dev_path = devs_path[ANONYM_NAME]
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


def create_app(dev_name, app_name):
    app_path = devs_path[dev_name].apps[app_name]
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
    draft_name = os.readlink(CURR_DRAFT_PATH)
    os.symlink(str(int(draft_name) + 1), NEXT_DRAFT_PATH)
    os.rename(NEXT_DRAFT_PATH, CURR_DRAFT_PATH)
    dev_name = dev_name or ANONYM_PREFIX + draft_name
    os.rename(DRAFTS_PATH + '/' + draft_name, devs_path[dev_name])
    create_app(dev_name, SAMPLE_NAME)
    open(locks_path[dev_name], 'w').close()
    return dev_name
