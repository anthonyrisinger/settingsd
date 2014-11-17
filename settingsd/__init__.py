# encoding: utf-8
"""
Stacked + fragmented implementation of settings.py

Simply create a settings.py file and add::
    >>> __import__('settingsd').replace(__name__)

or append __init__.py with::
    >>> settings = __import__('settingsd').install(__name__)

Modify __path__ (but do NOT replace!) in fragments to alter the search path.
"""


from __future__ import print_function
from __future__ import absolute_import


import sys
import pwd
import types
import pkgutil
import logging
import os.path

import collections
import re


class Globals(dict):

    def __init__(self, *args, **kwds):
        super(Globals, self).__init__(*args, **kwds)
        self.trip1 = set()
        self.trip2 = set()

    def __getitem__(self, key):
        # if UPPER, call get(...) instead to provide a default of None
        supr = super(Globals, self)
        value = supr.get(key) if key.isupper() else supr.__getitem__(key)
        return value

    def __setitem__(self, key, attr):
        if key.isupper():
            self.trip1.add(key)
            if key not in self or attr is not self[key]:
                self.trip2.add(key)
        super(Globals, self).__setitem__(key, attr)


class Settingsd(collections.Mapping, types.ModuleType):

    def __init__(self, keys):
        name = keys['__name__']
        super(Settingsd, self).__init__(name)
        defaults = {
            '__file__': None,
            '__path__': list(),
            '__package__': name,
            }
        defaults.update(
            keys,
            dist=collections.OrderedDict(),
            path=collections.OrderedDict(),
            conf=collections.OrderedDict(),
            )
        self.__dict__.update(defaults)
        if not self.__path__ and self.__file__:
            filename = self.__file__.strip('co')
            if filename.endswith('.py'):
                search = os.path.abspath(filename[:-2] + 'd')
                if os.path.isdir(search) or hasattr(self, '__loader__'):
                    self.__path__.append(search)

    def __enter__(self):
        sys.modules[self.__name__] = self
        return Globals(
            __name__=self.__name__,
            __path__=self.__path__,
            settings=self,
            sys=sys,
            os=os,
            )

    def __exit__(self, *exc_info):
        if exc_info != (None, None, None):
            # set as "configured"
            self.conf.setdefault('__EXCEPTION__', exc_info[1])
            if sys.modules.get(self.__name__) is self:
                sys.modules.pop(self.__name__)

    def __call__(self):
        if self.configured:
            return self

        with self as ctx:
            fqm = dict()
            dist = collections.defaultdict(list)
            path = collections.defaultdict(list)
            for importer, name, is_pkg in iter_modules(self.__path__):
                try:
                    fqm[name] = importer.path
                except AttributeError:
                    # zip packages
                    fqm[name] = os.path.join(
                        importer.archive,
                        importer.prefix,
                        ).rstrip('/')
                loader = importer.find_module(name)
                ctx['__file__'] = loader.get_filename(name)
                exec loader.get_code(name) in ctx
                while ctx.trip2:
                    dist[ctx.trip2.pop()].append(name)
            for k, v in sorted(dist.items()):
                self.dist[k] = tuple(v)
                path[fqm[v.pop()]].append(k)
            for p in self.__path__:
                self.path[p] = tuple(path[p])
            map(ctx.pop, set(ctx.keys()) - ctx.trip1)
            self.configure(**ctx)

        sep = '\n    '
        self.__file__ = sep + sep.join(self.__path__) + sep
        return self

    def show(self, prefix='[settings.d]', file=None):
        pfx = prefix and (str(prefix) + ' ') or ''
        fp = file or sys.stderr
        # ensure something to show
        self.configured or self()

        # dump PATHS
        print(pfx + 'PATH:', file=fp)
        for path in self.__path__:
            print(pfx + '    {0}'.format(path), file=fp)

        # dump KEYS by SOURCE
        print(pfx + 'SOURCE:', file=fp)
        for source, keys in self.source():
            if not keys:
                continue

            print(pfx + '    {0}'.format(source), file=fp)
            for key in keys:
                print(pfx + '        {0}'.format(key), file=fp)

        # dump FRAGMENTS by KEY
        print(pfx + 'TRACE:', file=fp)
        maxlen = list()
        joined = list()
        traces = self.trace()
        for key, frags in traces:
            join = ' | '.join(frags)
            joined.append((join, key + ' '))
            maxlen.append(len(key) + 1)
        maxlen = min(40, max(maxlen or [40]))
        for joins, key in joined:
            out = pfx + '    {0:.<{1}} {2}'.format(key, maxlen, joins)
            print(out, file=fp)

    def __dir__(self):
        try:
            keys = super(Settingsd, self).__dir__()
        except AttributeError:
            keys = dir(self.conf)
        keys.extend(self.conf)
        return keys

    def __getattr__(self, key):
        self.configured or self()
        for k in (key, key.upper()):
            if k in self.conf:
                return self.conf[k]

        return getattr(super(Settingsd, self), key)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __iter__(self):
        for key in self.conf:
            yield key

    def __len__(self):
        return len(self.conf)

    def trace(self, key=None):
        if key is not None:
            key = key.upper()
            if key in self.dist:
                return self.dist[key]
            return tuple()
        return tuple(self.dist.iteritems())

    def source(self, key=None):
        if key is not None:
            if key in self.path:
                return self.path[key]
            return tuple()
        return tuple(self.path.iteritems())

    def configure(self, *args, **kwds):
        # this ensures bool(self.conf) is True
        kwds.setdefault('CONFIGURED', True)
        return self.conf.update(kwds)

    @property
    def configured(self):
        return bool(self.conf)


def iter_modules(paths):
    """
    similar to pkgutil.iter_modules, but allows path to change/update
    """
    def regen(paths, cache_in, cache_out):
        matcher = re.compile('^([0-9]+)-(.+)')
        for importer, name, is_pkg in pkgutil.iter_modules(paths):
            match = matcher.match(name)
            if not match:
                continue

            key = (int(match.group(1)), match.group(2))
            if key not in cache_out:
                cache_in[key] = (importer, name, is_pkg)

        return cache_in, cache_out

    old_path = paths[:]
    cache_in, cache_out = regen(paths, dict(), dict())

    while cache_in:
        # probably inefficient...
        key = sorted(cache_in)[0]
        val = cache_out[key] = cache_in.pop(key)
        yield val

        # a block of code was executed, maybe regen cache
        if paths != old_path:
            old_path = paths[:]
            cache_in, cache_out = regen(paths, cache_in, cache_out)


def replace(module):
    if not hasattr(module, '__name__'):
        module = sys.modules[module]
    if not hasattr(module, '__name__'):
        raise TypeError('{0} must have a __name__'.format(module))

    settings = sys.modules[module.__name__] = Settingsd(vars(module))
    settings.origin = module
    return settings


def install(module, **kwds):
    if not hasattr(module, '__name__'):
        module = sys.modules[module]
    if not hasattr(module, '__name__'):
        raise TypeError('{0} must have a __name__'.format(module))

    ns = vars(module).copy()
    name = ns.pop('__name__')
    file = ns.pop('__file__')
    path = ns.pop('__path__')
    name = name + '.settings'
    if file:
        file = os.path.abspath(file)
        file = os.path.dirname(file)
        file = os.path.join(file, 'settings.py')
    ns['__name__'] = name
    ns['__file__'] = file
    ns.update(kwds)

    settings = sys.modules[name] = Settingsd(ns)
    settings.origin = module
    return settings
