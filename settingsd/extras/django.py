# encoding: utf8
"""
Descriptors for Django
"""

from __future__ import absolute_import
from __future__ import print_function

from .. import utils


def configure_on_ready(settings):
    from django.conf import settings as djsettings
    if not djsettings.configured:
        ns = utils.namespace(settings)
        djsettings.configure(**ns)


# TODO: should probably call super(...) somehow?
def fallback_to_defaults(settings, key):
    from django.apps import apps
    from django.conf import settings as djsettings

    if not key.isupper() or key.startswith('SETTINGSD_'):
        # FIXME: need to call super(...) first somehow
        raise AttributeError(key)

    if not djsettings.configured:
        ns = utils.namespace(settings)
        djsettings.configure(**ns)

    attr = getattr(djsettings, key)
    return attr


class LocateApps(object):
    """
    Proxies settings.app directly to django.apps
    """

    def __init__(self, app=None, models=True):
        self.__app = app
        self.__models = models

    def __getattr__(self, key):
        from django.apps import apps
        if self.__app:
            attr = apps.get_model(self.__app.label, key)
        else:
            attr = apps.get_app_config(key)
            if self.__models:
                attr = self.__class__(app=attr, models=self.__models)
        # cache attr lookup
        setattr(self, key, attr)
        return attr

    def __dir__(self):
        from django.apps import apps
        if self.__app:
            # prefer object_name over model_name to match ClassNaming
            attrs = [
                model._meta.object_name
                for model in self.__app.get_models()
                if not model._meta.proxy
                ]
        else:
            attrs = [
                app.label
                for app in apps.get_app_configs()
                ]
        return attrs


class ConfigureApps(object):

    def __init__(self, models=True):
        self.configured = False
        self.models = models

    def __get__(self, settings, owner):
        if settings is None:
            return self

        if self.configured:
            return LocateApps(models=self.models)

        import django
        from django.apps import apps
        from django.conf import settings as djsettings

        if not djsettings.configured:
            ns = utils.namespace(settings)
            djsettings.configure(**ns)
        if not apps.ready:
            django.setup()

        self.configured = True
        return LocateApps(models=self.models)

    def __set__(self, settings, value):
        raise AttributeError("can't set attribute")
