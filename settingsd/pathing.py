# encoding: utf8


from __future__ import absolute_import
from __future__ import print_function

import os
import pwd


def _name_to_parts(name):
    appdir, suffix = name.rsplit('.', 2)[-2:]
    suffix += '.d'
    return (appdir, suffix)


def root(ns, path, create=True, mode=0644):
    """
    Append an absolute path to ns['__path__']
    """
    parts = _name_to_parts(ns['__name__'])
    path_root = os.path.join(path, *parts)
    path_root = os.path.abspath(path_root)
    if create and not os.path.exists(path_root):
        try:
            os.makedirs(path_root, mode=mode)
        except OSError:
            pass

    return path_root


def home(ns, path=None, create=True, mode=0644, xdg=True):
    """
    Append a path to ns['__path__'] derived from $XDG_CONFIG_HOME
    """
    if xdg and os.environ.get('XDG_CONFIG_HOME'):
        path_home = os.environ['XDG_CONFIG_HOME']
    else:
        if os.environ.get('HOME'):
            path_home = os.environ['HOME']
        else:
            path_home = pwd.getpwuid(os.getuid()).pw_dir
        path_home = os.path.join(path_home, '.config')

    if path:
        path_home = os.path.join(path_home, path)
    parts = _name_to_parts(ns['__name__'])
    path_home = os.path.join(path_home, *parts)
    path_home = os.path.abspath(path_home)
    if create and not os.path.exists(path_home):
        try:
            os.makedirs(path_home, mode=mode)
        except OSError:
            pass

    return path_home


def default(ns, path=None, create=True, mode=0644):
    """
    Append a path to ns['__path__'] derived from ns['__file__']
    """
    path_file = os.path.abspath(ns['__file__'])
    path_file = os.path.dirname(path_file)
    path_file = os.path.dirname(path_file)

    if path:
        path_file = os.path.join(path_file, path)
    parts = _name_to_parts(ns['__name__'])
    path_file = os.path.join(path_file, *parts)
    path_file = os.path.abspath(path_file)
    if create and not os.path.exists(path_file):
        try:
            os.makedirs(path_file, mode=mode)
        except OSError:
            pass

    return path_file
