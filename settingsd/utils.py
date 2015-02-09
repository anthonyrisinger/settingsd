# encoding: utf8
"""
Utilities
"""


from __future__ import absolute_import
from __future__ import print_function

import collections
import os.path
import mimetypes
import re
import sys


def namespace(settings):
    """
    Return the namespace associated with these settings
    """
    if getattr(settings, 'SETTINGSD_NAMESPACE', False):
        # already a namespace
        return settings

    # expected to exist if passed anything else
    key = getattr(settings, 'SETTINGSD_NS')
    ns = getattr(settings, key)
    return ns


def resolve_bases(settings, bases):
    """
    Generate list of bases from strings or classes
    """
    ns = namespace(settings)
    resolved = list()

    for base in bases:
        if not isinstance(base, type):
            base = resolve_import(ns, base)
        resolved.append(base)

    resolved = tuple(resolved)
    return resolved


def resolve_import(settings, importable):
    ns = namespace(settings)
    level, module, attr = 0, importable, None

    # split off the attr
    if ':' in module:
        module, attr = module.rsplit(':', 1)

    # determine the relative import level, if any
    if module.startswith('.'):
        for i, c in enumerate(module):
            if c == '.':
                level = i + 1
                continue

            module = module[i:]
            break

    # perform import!
    importable = __import__(
        name=module,
        globals=ns,
        locals=ns,
        # as long as fromlist has *something*, we get the last module
        fromlist=[attr or '__class__'],
        level=level,
        )
    if attr:
        importable = getattr(importable, attr)

    return importable


def getopt(settings, key, strict=False, copy=False):
    """
    Get an option from settings or defaults with optional copy
    """
    from . import defaults

    ns = namespace(settings)
    if ns.__contains__(key):
        return ns.__getitem__(key)

    # usually fallback to None
    args = [defaults, key, None]
    if strict:
        args.pop()
    default = getattr(*args)
    if copy:
        from copy import deepcopy
        default = deepcopy(default)

    return default


def keys_from_uri(uri):
    keys = {'uri': uri}
    keys['head'], keys['tail'] = os.path.split(keys['uri'])
    keys['name'], keys['ext'] = os.path.splitext(keys['tail'])
    keys['mime'] = mimetypes.guess_type(keys['tail'])[0]
    matcher = re.compile('^_?([0-9]+)[-_](.+)$')
    match = matcher.match(keys['name'])
    if not match:
        return None

    keys['index'] = int(match.group(1))
    keys['key'] = match.group(2)
    keys['key'] = re.sub('[^0-9A-Za-z]', '_', keys['key'])
    keys['key'] = re.sub('_{2,}', '_', keys['key'])
    keys['key'] = keys['key'].upper()

    return keys


def ns_prepare(sources, install=True):
    """
    Unify an arbitrary number of sources into a namespace
    """
    ns = collections.OrderedDict()
    for source in sources:
        # if already a dict, do nothing
        if not hasattr(source, 'keys'):
            # maybe user passed __name__
            if hasattr(source, 'startswith'):
                source = sys.modules[source]
            # maybe we have a module
            if hasattr(source, '__dict__'):
                source = source.__dict__
                if install:
                    # if not replacing, we only want a couple attrs
                    source = {
                        '__name__': source.get('__name__'),
                        '__file__': source.get('__file__'),
                        '__package__': source.get('__package__'),
                        }
        # assume we have something compatible (iterator, dict, etc)
        ns.update(source)

    # install(...) must derive new values for some attributes
    if install:
        #FIXME: need to drop __path__ here if not explicitly set by user!
        ns.pop('__package__', None)
        ns_file = ns.pop('__file__', None)
        ns_package = ns.pop('__name__')
        ns_name = ns_package + '.settings'
        if ns_file:
            ns_file = os.path.dirname(ns_file)
            ns_file = os.path.join(ns_file, 'settings.py')
        ns['__package__'] = ns_package
        ns['__name__'] = ns_name
        ns['__file__'] = ns_file

    # ensure somewhat correct
    if not ns.get('__file__'):
        ns['__file__'] = None
    if not ns.get('__package__'):
        ns['__package__'] = ns['__name__'].rsplit('.', 1)[0]

    # prefer whatever user passes, even if empty
    if '__path__' not in ns:
        ns['__path__'] = list()
        if ns['__file__']:
            from . import path
            item = path.default(ns)
            ns['__path__'].append(item)

    for i, item in enumerate(ns['__path__']):
        while hasattr(item, '__call__'):
            item = item(ns)
        ns['__path__'][i] = item

    #TODO: necessary or just nice repr(...)?
    ns.pop('__builtins__', None)
    return ns


def settings_from_ns(ns, update=True):
    """
    Assemble settings from a namespace
    """
    from . import base

    # assemble settings
    settings_ns = base.Settingsd(ns)
    settings = settings_ns.instance

    if update:
        # update sys.modules with our settings
        sys.modules[settings.__name__] = settings
        parent = sys.modules[settings.__package__]
        if parent is not settings:
            # put settings on the parent module
            key = settings.__name__.rsplit('.', 1)[-1]
            setattr(parent, key, settings)
        for part in settings_ns.part:
            # update sys.modules with all its parts
            if part.__name__ != settings.__name__:
                sys.modules[part.__name__] = part

    return settings
