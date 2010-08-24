# (c) 2010 by Anton Korenyushkin

import os.path
import httplib
import mimetypes

from piston.handler import BaseHandler
from dulwich.repo import Repo
from dulwich.errors import NotGitRepository
from django.http import HttpResponse

from error import Error
from utils import read_file
from paths import DEVS_PATH


def _get_libs_path(dev_name, owner_name):
    owner_path = DEVS_PATH[owner_name]
    if owner_name == dev_name:
        return owner_path.apps
    if not os.path.exists(owner_path):
        raise Error(
            'The developer "%s" doesn\'t exist.' % owner_name,
            status=httplib.NOT_FOUND)
    return owner_path.libs


class OwnerHandler(BaseHandler):
    allowed_methods = ('GET')

    def get(self, request, owner_name):
        libs_path = _get_libs_path(request.dev_name, owner_name)
        return [
            read_file(libs_path[lower_name].name)
            for lower_name in sorted(os.listdir(libs_path))
        ]


def _get_repo(dev_name, owner_name, lib_name):
    libs_path = _get_libs_path(dev_name, owner_name)
    try:
        return Repo(libs_path[lib_name].git)
    except NotGitRepository:
        raise Error(
            'The library "%s/%s" doesn\'t exist.' % (owner_name, lib_name),
            status=httplib.NOT_FOUND)


_TAG_PREFIX = 'refs/tags/'
_BRANCH_PREFIX = 'refs/heads/'


class LibHandler(BaseHandler):
    allowed_methods = ('GET')

    def get(self, request, owner_name, lib_name):
        repo = _get_repo(request.dev_name, owner_name, lib_name)
        versions = set()
        for ref_name in repo.refs.keys():
            if '/' not in ref_name:
                versions.add(ref_name)
            elif ref_name.startswith(_TAG_PREFIX):
                versions.add(ref_name[len(_TAG_PREFIX):])
            elif ref_name.startswith(_BRANCH_PREFIX):
                versions.add(ref_name[len(_BRANCH_PREFIX):])
        return sorted(list(versions))


def _get_tree(repo, version):
    for ref_name in (version, _TAG_PREFIX + version, _BRANCH_PREFIX + version):
        try:
            sha = repo.refs[ref_name]
        except KeyError:
            continue
        obj = repo.get_object(sha)
        while obj.type_name == 'tag':
            obj = repo.get_object(obj.object[1])
        if obj.type_name == 'commit':
            return repo.get_object(obj.tree)
    raise Error(
        'The version "%s" doesn\'t exist.' % version, status=httplib.NOT_FOUND)


def _traverse(repo, tree):
    result = {}
    for name, _, sha in tree.iteritems():
        obj = repo.get_object(sha)
        result[name] = (
            _traverse(repo, obj) if obj.type_name == 'tree' else None)
    return result


class VersionHandler(BaseHandler):
    allowed_methods = ('GET')

    def get(self, request, owner_name, lib_name, version):
        repo = _get_repo(request.dev_name, owner_name, lib_name)
        return _traverse(repo, _get_tree(repo, version))


class BlobHandler(BaseHandler):
    allowed_methods = ('GET')

    def get(self, request, owner_name, lib_name, version, path):
        repo = _get_repo(request.dev_name, owner_name, lib_name)
        obj = _get_tree(repo, version)
        for name in path.split('/'):
            if obj.type_name == 'tree':
                try:
                    sha = obj[name][1]
                except KeyError:
                    pass
                else:
                    obj = repo.get_object(sha)
                    continue
            raise Error(
                'The file "%s" doesn\'t exist.' % path,
                status=httplib.NOT_FOUND)
        if obj.type_name != 'blob':
            raise Error('"%s" is a folder.' % path)
        return HttpResponse(obj.data, mimetypes.guess_type(path)[0])
