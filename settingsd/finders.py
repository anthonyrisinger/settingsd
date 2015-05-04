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
    for name in sorted(os.listdir(path)):
        part = {'uri': os.path.join(path, name)}

        def get_data(part=part):
            with open(part['uri']) as fp:
                return fp.read()

        part['get_data'] = get_data
        parts.append(part)

    return parts


def zipfile(settings, path):
    import zipimport

    try:
        # abuse zipimport over zipfile because it's faster and potentially
        # cached if we are already operating/importing from the archive
        importer = zipimport.zipimporter(path)
    except zipimport.ZipImportError:
        return None

    parts = list()
    for info in sorted(importer._files.values()):
        if not info[0].startswith(path):
            # random item in archive we don't care about
            continue

        part = {'uri': info[0]}

        def get_data(part=part):
            return importer.get_data(part['uri'])

        part['get_data'] = get_data
        parts.append(part)

    return parts
