"""
Common OpenGL functionality.
"""
from OpenGL import GL
import rave.log
from .math import ortho, identity
from .versions import get_version_range


def dump_info(context):
    context.make_current()
    _log('OpenGL context: {profile} {major}.{minor}', profile=context.profile, major=context.major, minor=context.minor)
    _log('OpenGL vendor: {vendor}', vendor=GL.glGetString(GL.GL_VENDOR).decode('utf-8'))
    _log('OpenGL renderer: {renderer}', renderer=GL.glGetString(GL.GL_RENDERER).decode('utf-8'))
    _log('OpenGL driver: {version}', version=GL.glGetString(GL.GL_VERSION).decode('utf-8'))


## Internals.

_log = rave.log.get(__name__)
