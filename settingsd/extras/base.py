# encoding: utf8
"""
Common descriptors for user code
"""

from __future__ import absolute_import
from __future__ import print_function

from .. import utils


__all__ = ['KeyMoved']


class KeyMoved(object):

    def __init__(self, key):
        self.key = key

    def __get__(self, settings, owner):
        if settings is None:
            return self

        ns = utils.namespace(settings)
        attr = ns[self.key]
        return attr

    def __set__(self, settings, value):
        ns = utils.namespace(settings)
        ns[self.key] = value
