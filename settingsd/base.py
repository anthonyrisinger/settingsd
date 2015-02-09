# encoding: utf8
"""
Core things
"""


from __future__ import absolute_import
from __future__ import print_function

import collections
import os.path
import types

from . import defaults
from . import utils


class Namespace(object):

    # used by utils.getopt(...) to prevent recursion
    SETTINGSD_NAMESPACE = True


#FIXME: issubclass(BaseSettings, types.ModuleType)
class BaseSettings(object):
    """
    Default implementation of SETTINGSD_BASES
    """

    def __repr__(self):
        rv = '<module {0.__name__!r} from {0.__file__!r}>'.format(self)
        return rv

    def __contains__(self, key):
        rv = key in utils.namespace(self)
        return rv

    def __getitem__(self, key):
        rv = utils.namespace(self)[key]
        return rv

    def __iter__(self):
        #FIXME: should this only consider isupper() keys?
        rv = iter(utils.namespace(self))
        return rv

    def __len__(self):
        #FIXME: should this only consider isupper() keys?
        rv = len(utils.namespace(self))
        return rv


class Settingsd(Namespace, collections.OrderedDict):

    # these can also be imported by user code
    from .api import show
    from .api import source
    from .api import trace

    def __init__(self, *args, **kwds):
        # use a temp OrderedDict to initialize the first part
        ns = collections.OrderedDict(*args, **kwds)
        part = types.ModuleType(ns['__name__'])
        part.__dict__.update(ns)
        self.part = [part]
        self.dist = collections.OrderedDict()
        self.path = collections.OrderedDict()
        self.type_overrides = dict()
        super(Settingsd, self).__init__(ns)
        self.__import__()

    def __getitem__(self, key):
        try:
            # pass super(...) object because getopt will try to self[key]
            supr = super(Settingsd, self)
            item = utils.getopt(
                supr, key,
                strict=not key.isupper(),
                copy=True,
                )
        except AttributeError as e:
            raise KeyError(key)

        return item

    def __setitem__(self, key, attr):
        if key == '__doc__':
            # TODO: record each parts doc (JSON/etc) and assemble at end
            self.part[-1].__doc__ = attr and attr.strip()
            return

        supr = super(Settingsd, self)
        if key.isupper() and not key[0].isdigit() and (
                key not in self or attr is not self[key]
                ):
            # record this SETTINGS_KEY
            part = self.part[-1]
            partname = part.__name__.rsplit('.', 1)[-1]
            partpath = os.path.dirname(part.__file__)
            if key not in self.dist:
                self.dist[key] = list()
            if partpath not in self.path:
                self.path[partpath] = list()
            self.dist[key].append(partname)
            self.path[partpath].append(key)
            setattr(part, key, attr)
        supr.__setitem__(key, attr)

    @property
    def instance(self):
        # derive a name for our custom subclass
        name = self['__name__'].replace('.', ' ').title().replace(' ', '')
        key = utils.getopt(self, 'SETTINGSD_NS')
        bases = utils.getopt(self, 'SETTINGSD_BASES')
        bases = utils.resolve_bases(self, bases)
        attrs = dict(self, **self.type_overrides)
        if not attrs.get('SETTINGSD_NS'):
            # avoid recursion in utils.(namespace|getopt)
            attrs['SETTINGSD_NS'] = key
        # functions in __dict__ shadow those in __class__
        attrs = _find_and_proxy_methods(attrs)
        # construct said subclass and instantiate
        #FIXME: should class and/or instance be cached?
        settings = type(name, bases, attrs)
        settings.__module__ = self['__package__']
        settings = settings()
        if key:
            #FIXME: would Falsey lead to GC self???
            setattr(settings, key, self)

        # if user defined ready(...), call it now
        if hasattr(settings, 'ready'):
            if hasattr(settings.ready, '__call__'):
                settings.ready()

        return settings

    def __import__(self):
        # save original value
        file_orig = self['__file__']

        for info in self.iter_parts():
            name = self['__name__'] + '.' + info['name']
            part = self[info['name']] = types.ModuleType(name)
            self.part.append(part)
            self['__file__'] = part.__file__ = info['uri']

            # search each loader in order until a match is found
            loader = None
            for loader in utils.getopt(self, 'SETTINGSD_LOADERS'):
                loader = utils.resolve_import(self, loader)(self, info)
                if loader:
                    # loader could be a simple function, such as executing
                    # python code in our namespace, but the loader might also
                    # be a descriptor designed to handle a single key
                    if hasattr(loader, '__get__'):
                        self.type_overrides[info['key']] = loader
                        self[info['key']] = info['uri']
                    # loader found and done processing part
                    break

            if not loader:
                # unable to find a specialty loader; store the path
                self[info['key']] = info['uri']

        # restore original value
        self['__file__'] = file_orig
        #TODO: useful?
        #self.pop('__import__')

    def iter_parts(self):
        """
        similar to pkgutil.iter_modules, but allows path to change/update
        """
        def regen(paths, cache_in, cache_out):
            for path in paths:
                try:
                    #TODO: delegate to Adapters
                    parts = [
                        os.path.join(path, part)
                        for part in os.listdir(path)
                        ]
                except OSError:
                    #TODO: handle zip packages
                    continue

                for part in parts:
                    keys = utils.keys_from_uri(part)
                    if not keys:
                        continue

                    cache_key = (keys['index'], keys['name'])
                    if cache_key not in cache_out:
                        cache_in[cache_key] = keys

            return cache_in, cache_out

        old_path = self['__path__'][:]
        cache_in, cache_out = regen(self['__path__'], dict(), dict())

        while cache_in:
            # probably inefficient...
            key = sorted(cache_in)[0]
            val = cache_out[key] = cache_in.pop(key)
            yield val

            # a block of code was executed, maybe regen cache
            if self['__path__'] != old_path:
                old_path = self['__path__'][:]
                cache_in, cache_out = regen(
                    self['__path__'],
                    cache_in,
                    cache_out,
                    )


class MethodFromDictFunction(object):

    def __init__(self, key):
        self.key = key

    def __get__(self, settings, owner):
        if settings is None:
            return self

        ns = utils.namespace(settings)
        fun = ns[self.key]
        # all functions are descriptors that bind to the instance
        method = fun.__get__(settings, settings.__class__)
        return method

    def __set__(self, settings, attr):
        raise AttributeError("can't set attribute")


def _find_and_proxy_methods(attrs):
    for fun_name, fun in attrs.items():
        if fun_name.startswith('__') and fun_name.endswith('__'):
            # leave it alone
            continue

        if not hasattr(fun, '__call__'):
            # not a callable
            continue

        if not hasattr(fun, '__globals__'):
            # not a function
            continue

        if hasattr(fun, '__self__'):
            # already bound to something else
            continue

        # this thing looks like a function intended to be a method
        attrs[fun_name] = MethodFromDictFunction(fun_name)

    return attrs
