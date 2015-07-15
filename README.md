# settingsd

## Introduction
settingsd is a drop-in replacement for a traditional `settings.py` module. It allows settings to be logically
separated into different files, optionally from multiple paths, and reassembled in a predictable order. It's primary use
is enabling production/qa/staging code to run with alternate settings, in a consistent fashion, without introducing
additional overhead during development.


## How it works
It helps to have a loose understanding of how python packages behave, as well as similar Unix concepts (`/etc/sy
sctl.d`, `/etc/pam.d`, etc), but is not necessary. Without delving into implementation details, [settingsd](http://github.com/xtfxme/settingsd) aspires
to behave like this:

```python
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
 # while loading, NameError -> None
 TOMATO_COLOR = 'red'
```

Per above, the flow is roughly:

  * use __path__ to locate directories to scan
  * identify all "submodules" and sort by name
  * execute each module in the same primary namespace

## How to use
Setup settingsd from your __init__.py:

```python
import settingsd
settings = settingsd.install(__name__)
```

By default, if the enclosing module has a valid __file__ and one is not specified via keyword to install(...), s
ettingsd will use that to compute a default search path. You may control the search path explicitly with:

```python
settings = settingsd.install(__name__, __path__=['settings.d'])
```

Any keywords passed to install(...) will be preferred and set on your settings module. You may also use list
methods to affect __path__:

```python
settings.append('/home/me/settings.d')
```

Common some dynamic paths have symbolic names for convenience:
```python
settings.append('@home')
```

Which expands to `${XDG_CONFIG_HOME}/{__name__}/settings.d`

## Parts
Part files are any file within the search path matching the following pattern:
`([0-9])+(@[a-z]+)?-[^.].py`
IOW, it must start with a number, followed by an optional load hint, a dash, a string of pretty much anything except
periods, and end in `.py`. A future version of settingsd will allow part files to end in any suffix, and select an appropriate load hint accordingly (eg. a txt file would use the @path hint).

_Examples_:
```
10-rubber-bands.py
99-debug.py
35@path-HTTPS-CERT.py
```

_Load Hints_:

Aside from importing python files, settingsd allows you to map a file path or contents to a key by using a "load
hint". A load hint instructs settingsd on how to handle the part file. The default hint is @code, which aptly means
"execute this file as python code".

The following hints are currently supported:

`@code`: execute the part within the primary namespace

Example:
`99@code-debug.py`

`@path`: use the part's name to derive a key, and set the key to the parts absolute path

Example:
`35@path-HTTPS-CERT.py`

`@file`: use the part's name to derive a key, and set the key to the parts contents

Example:
`35@file-IDP-CERT.py`

Hints exist to boost interoperability with external tools; a tool like Chef can simply drop a standard PEM certificate in
the search path with the appropriate name and it will be loaded into the desired key for use by the application.

## Future

Soon settingsd will allow you to import descriptors and anything else into your part files, and upon
assembly/execution, create a new type(...) for you. This means, from a part file, you can do something like:
```python
from settingsd.contrib.django import AppFinder
app = AppFinder()
```
Then in your application do something like this:
```python
from payback import settings
groups = settings.app.access.Group.objects.all()
```
IOW, your part files will literally behave as if they we executed within a class definition, and an instance of the
resulting class will become your settings object!
