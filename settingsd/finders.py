# encoding: utf8
"""
Finders
"""

from __future__ import absolute_import
from __future__ import print_function

from . import utils


def directory(settings, path):
    import os

    if not os.path.isdir(path):
        return None

    parts = list()
    for name in os.listdir(path):
        part = {'uri': os.path.join(path, name)}

        def get_data(part=part):
            with open(part['uri']) as fp:
                return fp.read()

        part['get_data'] = get_data
        parts.append(part)

    return parts
