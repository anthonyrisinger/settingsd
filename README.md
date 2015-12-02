# settingsd

## Introduction
settingsd is a drop-in replacement for a traditional `settings.py` module. It allows settings to be logically
separated into different files, optionally from multiple paths, and reassembled in a predictable order. It's primary use
is enabling production/qa/staging code to run with alternate settings, in a consistent fashion, without introducing
additional overhead during development.

## How it works

It helps to have a loose understanding of how python packages behave, as well as similar Unix concepts (`/etc/sysctl.d`, `/etc/pam.d`, etc), but is not necessary. Without delving into implementation details, [settingsd](http://github.com/xtfxme/settingsd) aspires
to behave like this:

```python
class ApplicationSettings(type.ModuleType):

    __path__ = ['settings.d']
    # settings.d/01-apple.py
    APPLE_COLOR = 'red'
    # settings.d/02-banana.py
    BANANA_COLOR = 'yellow'
    # settings.d/03-production.py
    __path__.insert(0, '/production/settings.d')
    # settings.d/04-orange.py (NOT LOADED!)
    #ORANGE_COLOR = 'orange'
    # /production/settings.d/04-orange.py
    ORANGE_COLOR = 'purple'
    # settings.d/05-tomato.py
    if not TOMATO_COLOR:
        # NameErrors transformed into None during assembly
        TOMATO_COLOR = 'red'

sys.modules['application.settings'] = ApplicationSettings()
```

Per above, the flow is roughly:

  * Use `__path__` to locate directories to scan
  * Identify all "modules" and sort by name
  * Execute selected "modules" in the same primary namespace
  * Convert said namespace to a new `type()`
  * Create one instance and install into `sys.modules`

## How to use
Setup settingsd from your `__init__.py`:

```python
import settingsd
settings = settingsd.install(__name__)
```

By default, if the enclosing module has a valid `__file__` and one is not specified via keyword to `install()`, settingsd will use that to compute a default search path. You may control the search path explicitly with:

```python
settings = settingsd.install(__name__, __path__=['settings.d'])
```
Keywords passed to `install()` simply seed the namespace.

settingsd allows you to import descriptors and anything else within part files:
```python
from settingsd.extras.django import ConfigureApps
app = ConfigureApps()
```

`ConfigureApps` is a property "activated" naturally when the namespace is converted to a class:

```python
from application import settings
groups = settings.app.access.Group.objects.all()
```

Part files behave as if they were executed within a class definition so you are free to define settings-bound methods:

```python
def echo(settings, *args, **kwds):
    print((settings, args, kwds))
```

And the usercode:

```python
from application import settings
groups = settings.echo('hello', who=me)
```

Special methods are no different:

```python
from settingsd.extras.django import fallback_to_defaults as __getattr__
```

Usercode:

```python
from application import settings
settings.SOME_DEFAULT_DJANGO_SETTING_YOU_DID_NOT_DEFINE_BUT_WILL_EXIST_ANYWAY
```
