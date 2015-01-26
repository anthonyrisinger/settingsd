# encoding: utf-8
"""
Stacked + fragmented implementation of settings.py

Simply create a settings.py file and add::
    >>> __import__('settingsd').replace(__name__)

or append __init__.py with::
    >>> settings = __import__('settingsd').install(__name__)

Modify __path__ in fragments to alter the search path.
"""


from __future__ import absolute_import
from __future__ import print_function

from . import utils


# PUBLIC API
__all__ = ['install', 'replace']


def install(*args, **kwds):
    """
    Install settings into another module, eg. called from myapp/__init__.py
    """
    ns = utils.ns_prepare(args + (kwds,), install=True)
    settings = utils.settings_from_ns(ns, update=True)
    return settings


def replace(*args, **kwds):
    """
    Replace module with settings, eg. called from myapp/settings.py
    """
    ns = utils.ns_prepare(args + (kwds,), install=False)
    settings = utils.settings_from_ns(ns, update=True)
    return settings
