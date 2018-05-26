"""
OpenGL 3.x backend for rave.
"""
import sys

import rave.log
import rave.backends

from .. import common
from . import shaders
from .window import create_gl_window
from .texture import Texture, Image

__provides__ = [ 'opengl' ]
__requires__ = [ 'opengl_manager' ]
BACKEND_PRIORITY = 50


## Module API.

def load(opengl_manager):
    global _manager
    _manager = opengl_manager
    _log('OpenGL manager: {}', _manager.__name__)

    rave.backends.register(rave.backends.BACKEND_VIDEO, sys.modules[__name__])

def load_backend(category):
    # Attempt to load a GL context to see if we support it. If we don't, create_window() will raise an exception.
    window = create_window('OpenGL Test', 1, 1, testing=True, visible=False)
    window.close()

def unload():
    global _manager
    _manager = None

    rave.backends.remove(rave.backends.BACKEND_VIDEO, sys.modules[__name__])


## Video backend API.

def create_window(*args, testing=False, **kwargs):
    window = _manager.create_window(*args, **kwargs)
    _manager.create_gl_context(window, common.get_version_range('core', (3, 0), (3, 3)))

    if not testing:
        # Dump some info.
        common.dump_info(window.gl_context)
    return window

def handle_events():
    _manager.handle_events()

def create_drawable(data):
    texture = Texture(data.width, data.height, data.get_data())
    return Image(texture)


## Internals.

_log = rave.log.get(__name__)
_manager = None
