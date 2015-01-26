# encoding: utf8
"""
Public API methods
"""


from __future__ import absolute_import
from __future__ import print_function

import sys

from . import utils


__all__ = ['trace', 'source', 'show']


def trace(self, key=None):
    ns = utils.namespace(self)
    if key is not None:
        key = key.upper()
        if key in ns.dist:
            return ns.dist[key]
        return tuple()
    return tuple(ns.dist.iteritems())


def source(self, key=None):
    ns = utils.namespace(self)
    if key is not None:
        if key in ns.path:
            return ns.path[key]
        return tuple()
    return tuple(ns.path.iteritems())


def show(self, prefix='[settings.d]', file=None):
    ns = utils.namespace(self)
    pfx = prefix and (str(prefix) + ' ') or ''
    fp = file or sys.stderr

    # dump PATHS
    print(pfx + 'PATH:', file=fp)
    for path in ns['__path__']:
        print(pfx + '    {0}'.format(path), file=fp)

    # dump KEYS by SOURCE
    print(pfx + 'SOURCE:', file=fp)
    for source, keys in ns.source():
        if not keys:
            continue

        print(pfx + '    {0}'.format(source), file=fp)
        for key in keys:
            print(pfx + '        {0}'.format(key), file=fp)

    # dump FRAGMENTS by KEY
    print(pfx + 'TRACE:', file=fp)
    maxlen = list()
    joined = list()
    traces = ns.trace()
    for key, frags in traces:
        join = ' | '.join(frags)
        joined.append((join, key + ' '))
        maxlen.append(len(key) + 1)
    maxlen = min(40, max(maxlen or [40]))
    for joins, key in joined:
        out = pfx + '    {0:.<{1}} {2}'.format(key, maxlen, joins)
        print(out, file=fp)
