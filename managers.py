# (c) 2010 by Anton Korenyushkin

import os
import os.path
import shutil
import socket

from error import Error
from utils import read_file, write_file, touch_file, get_id, execute_sql
from paths import (
    ANONYM_PREFIX, SAMPLE_NAME, SAMPLE_PATH, INITIAL_ENV_NAME, ROOT)

from git import GitRunner


CREATE_SCHEMA_SQL = 'SELECT ak.create_schema(%s);'


def create_app(dev_name, app_name):
    app_path = ROOT.devs[dev_name].apps[app_name]
    if os.path.isdir(app_path):
        raise Error(
            'The app "%s" already exists.' % read_file(app_path.name),
            'App name must be case-insensitively unique.')
    release_schema_name = get_id(dev_name, app_name)
    execute_sql(
        CREATE_SCHEMA_SQL * 2,
        (release_schema_name, release_schema_name + ':debug'))
    os.mkdir(app_path)
    write_file(app_path.name, app_name)
    shutil.copytree(SAMPLE_PATH, app_path.code)
    os.mkdir(app_path.git)
    os.mkdir(app_path.envs)
    write_file(app_path.envs[INITIAL_ENV_NAME], INITIAL_ENV_NAME)
    write_file(app_path.domains, '[]')
    git_runner = GitRunner(dev_name, app_name, 'akshell', 'akshell@akshell.com')
    git_runner.run('init', '--quiet')
    git_runner.run('add', '.')
    git_runner.run('commit', '--quiet', '-m', 'Initial commit.')


def create_dev(dev_name=None):
    draft_name = os.readlink(ROOT.drafts.curr)
    os.symlink(str(int(draft_name) + 1), ROOT.drafts.next)
    os.rename(ROOT.drafts.next, ROOT.drafts.curr)
    dev_name = dev_name or ANONYM_PREFIX + draft_name
    dev_path = ROOT.devs[dev_name]
    os.rename(ROOT.drafts[draft_name], dev_path)
    os.symlink('../apps', dev_path.grantors[dev_name])
    touch_file(ROOT.locks[dev_name])
    execute_sql(
        'CREATE TABLESPACE "%s" LOCATION \'%s\''
        % (dev_name.lower(), dev_path.tablespace))
    create_app(dev_name, SAMPLE_NAME)
    return dev_name


def send_to_ecilop(header, body=None):
    assert len(header) < 128
    padded_header = header + ' ' * (128 - len(header))
    sock = socket.socket(socket.AF_UNIX)
    sock.connect(ROOT.ecilop_socket)
    if body is None:
        sock.sendall(padded_header)
        sock.close()
        return
    sock.sendall((padded_header + body).encode('utf-8'))
    sock.shutdown(socket.SHUT_WR)
    parts = []
    while True:
        part = sock.recv(8192)
        if part:
            parts.append(part)
        else:
            break
    sock.close()
    return ''.join(parts)


def stop_patsaks(host_id):
    send_to_ecilop('STOP ' + host_id)


def _get_names(path):
    return [
        read_file(path[lower_name].name)
        for lower_name in sorted(os.listdir(path))
    ]


def get_app_names(dev_name):
    return _get_names(ROOT.devs[dev_name].apps)


def get_lib_names(dev_name):
    return _get_names(ROOT.devs[dev_name].libs)


def read_config(dev_name):
    return read_file(ROOT.devs[dev_name].config)
