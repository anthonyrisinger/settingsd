# encoding: utf8
"""
Loaders
"""

from __future__ import absolute_import
from __future__ import print_function

from . import utils


def from_name(settings, keys):
    loader = _load_from(settings, keys, 'name')
    return loader


def from_mime(settings, keys):
    loader = _load_from(settings, keys, 'mime')
    return loader


def from_ext(settings, keys):
    loader = _load_from(settings, keys, 'ext')
    return loader


def _load_from(settings, keys, suffix):
    datum = keys[suffix.lower()]
    opt = 'SETTINGSD_LOADER_FROM_' + suffix.upper()
    registry = utils.getopt(settings, opt)
    loader = registry.get(datum)
    if loader and not hasattr(loader, '__call__'):
        loader = utils.resolve_import(settings, loader)
    if loader:
        loader = loader(settings, keys)
    return loader


def python(settings, keys):
    ns = utils.namespace(settings)
    #TODO: zip files
    with open(keys['uri']) as fp:
        code = fp.read()
    #TODO: SETTINGSD_COMPILE_FLAGS
    code = compile(code, keys['uri'], 'exec')
    # eval can handle code objects compiled with exec (python[23])
    eval(code, ns)
    # signal successful loading
    return True


def json(settings, keys):
    ns = utils.namespace(settings)
    #TODO: zip files
    with open(keys['uri']) as fp:
        from json import load
        new_ns = load(fp=fp)
    # ensure stable load ordering
    for k in new_ns:
        ns[k] = new_ns[k]
    return True


class JSONLoader(object):

    def __init__(self, settings, keys):
        self.keys = keys
        self.cache = None

    def __get__(self, settings, owner):
        if settings is None:
            return self

        if not self.cache:
            #TODO: zip files
            with open(self.keys['uri']) as fp:
                from json import load
                self.cache = load(fp=fp)
        return self.cache

    def __set__(self, settings, value):
        pass
