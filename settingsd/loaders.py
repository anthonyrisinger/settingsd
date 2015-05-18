# encoding: utf8
"""
Loaders
"""

from __future__ import absolute_import
from __future__ import print_function

from . import utils


def from_key(settings, keys):
    loader = _load_from(settings, keys, 'key')
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
    #TODO: SETTINGSD_COMPILE_FLAGS
    code = keys['get_data']()
    code = compile(code, keys['uri'], 'exec')
    # eval can handle code objects compiled with exec (python[23])
    eval(code, ns)
    # signal successful loading
    return True


def json(settings, keys):
    from json import loads
    ns = utils.namespace(settings)
    new_ns = keys['get_data']()
    if not hasattr(new_ns, 'keys'):
        new_ns = loads(new_ns)
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
            from json import loads
            data = keys['get_data']()
            self.cache = loads(data)

        return self.cache

    def __set__(self, settings, value):
        pass
