# encoding: utf8
"""
Defaults for internal SETTINGSD_* keys
"""

from __future__ import absolute_import
from __future__ import print_function


SETTINGSD_NS = '__dict__'

SETTINGSD_BASES = ['settingsd.base:BaseSettings']

SETTINGSD_FINDERS = [
    'settingsd.finders:directory',
    'settingsd.finders:zipfile',
    ]

SETTINGSD_LOADERS = [
    'settingsd.loaders:from_key',
    'settingsd.loaders:from_mime',
    'settingsd.loaders:from_ext',
    ]

SETTINGSD_LOADER_FROM_EXT = dict()
SETTINGSD_LOADER_FROM_KEY = dict()
SETTINGSD_LOADER_FROM_MIME = {
    'text/x-python': 'settingsd.loaders:python',
    'application/json': 'settingsd.loaders:json',
    }
