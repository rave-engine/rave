import sdl2
import sdl2.ext
from ctypes import c_float, c_int, byref

import rave.log
import rave.events
import rave.rendering

__requires__ = [ 'opengl' ]



## Module API.

def load(opengl):
    global _gl
    _gl = opengl

def unload():
    global _gl
    _gl = None


## GL stuff.

GL_PROFILE_NAMES = {
    sdl2.SDL_GL_CONTEXT_PROFILE_CORE: 'core',
    sdl2.SDL_GL_CONTEXT_PROFILE_ES: 'ES',
    sdl2.SDL_GL_CONTEXT_PROFILE_COMPATIBILITY: 'compat'
}
GL_PROFILE_CONSTANTS = { v: k for k, v in GL_PROFILE_NAMES.items() }


## OpenGL manager API.

class Window(rave.rendering.Drawable):
    def __init__(self, handle, title, width, height, fullscreen, borders, resizable, vsync):
        self.handle = handle
        self.id = sdl2.SDL_GetWindowID(self.handle)
        self.gl_context = None
        self.gl_window = None
        self._title = title
        self._size = (width, height)
        self._drawable_size = (width, height)
        self._render_size = (width, height)
        self._fullscreen = fullscreen
        self._borders = borders
        self._resizable = resizable
        self._vsync = vsync

        rave.events.hook('video.window.resized', self.on_resize)
        rave.events.hook('video.window.close', self.on_close)

    def __del__(self):
        self.close()


    ## API.

    def close(self):
        if self.gl_context:
            self.gl_context.close()
            self.gl_context = None
        if self.handle:
            sdl2.SDL_DestroyWindow(self.handle)
            self.handle = None

    def show(self):
        sdl2.SDL_ShowWindow(self.handle)

    def hide(self):
        sdl2.SDL_HideWindow(self.handle)

    def minimize(self):
        sdl2.SDL_MinimizeWindow(self.handle)

    def maximize(self):
        sdl2.SDL_MaximizeWindow(self.handle)

    def restore(self):
        sdl2.SDL_RestoreWindow(self.handle)

    def render(self, target):
        if self.gl_context:
            self.gl_context.make_current()
            self.gl_window.render(target)
            self.gl_context.swap()

    def refresh(self):
        pass

    def add_layer(self, layer):
        if self.gl_window:
            self.gl_window.add_layer(layer)

    def get_layer(self, name):
        if self.gl_window:
            return self.gl_window.get_layer(name)

    def enable_gl(self, context, window):
        self.gl_context = context
        self.gl_window = window
        if self._vsync:
            try:
                self.vsync = True
            except Exception as e:
                _log.warn('Could not enable vsync for window: {}', e)
                self.vsync = False


    ## Events.

    def on_resize(self, event, window, w, h):
        if window and window != self.id:
            return
        self._size = (w, h)

        # Update drawable size with SDL info.
        if self.gl_context:
            w, h = c_int(), c_int()
            sdl2.SDL_GL_GetDrawableSize(self.handle, byref(w), byref(h))
            w, h = w.value, h.value
        self._render_size = (w, h)

    def on_close(self, event, window):
        if window and window != self.id:
            return
        self.close()
        rave.events.emit('game.stop')


    ## Properties.

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, new):
        sdl2.SDL_SetWindowTitle(self.handle, new.encode('utf-8'))
        self._title = new

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, new):
        sdl2.SDL_SetWindowSize(self.handle, *new)
        self._size = new

    @property
    def render_size(self):
        return self._render_size

    @property
    def scale(self):
        return self._render_size[0] / self._size[0]

    @property
    def fullscreen(self):
        return self._fullscreen

    @fullscreen.setter
    def fullscreen(self, new):
        if new:
            sdl2.SDL_SetWindowFullscreen(self.handle, sdl2.SDL_WINDOW_FULLSCREEN)
        else:
            sdl2.SDL_SetWindowFullscreen(self.handle, 0)
        self._fullscreen = new

    @property
    def borders(self):
        return self._borders

    @borders.setter
    def borders(self, new):
        sdl2.SDL_SetWindowBordered(int(new))
        self._borders = new

    @property
    def resizable(self):
        return self._resizable

    @property
    def vsync(self):
        # SDL_GL_GetSwapInterval() is not reliable, so return cached value.
        return self._vsync

    @vsync.setter
    def vsync(self, new):
        if self.gl_context:
            if new:
                try:
                    # Try late swap tearing first, which is not supported on all platforms.
                    self.gl_context.set_vsync(-1)
                except:
                    self.gl_context.set_vsync(1)
                self._vsync = True
            else:
                self.gl_context.set_vsync(0)
                self._vsync = False


class Context:
    CURRENT = None

    def __init__(self, window, handle, profile, major, minor):
        self.window = window
        self.context = handle
        self.profile = profile
        self.major = major
        self.minor = minor

    def __del__(self):
        self.close()

    def close(self):
        if self.context:
            sdl2.SDL_GL_DeleteContext(self.context)
            self.context = None

    def bind_texture(self, texture):
        self.make_current()

        width = c_float()
        height = c_float()
        if sdl2.SDL_GL_BindTexture(texture, byref(width), byref(height)) < 0:
            raise sdl2.ext.SDLError()
        return width.value, height.value

    def unbind_texture(self, texture):
        self.make_current()
        if sdl2.SDL_GL_UnbindTexture(texture) < 0:
            raise sdl2.ext.SDLError()

    def has_extension(self, name):
        self.make_current()
        return bool(sdl2.SDL_GL_ExtensionSupported(name))

    def get_function_address(self, name):
        self.make_current()
        return sdl2.SDL_GL_GetProcAddress(name)

    def make_current(self):
        if self.CURRENT is self:
            return

        if sdl2.SDL_GL_MakeCurrent(self.window, self.context) < 0:
            raise sdl2.ext.SDLError()
        self.CURRENT = self

    def set_vsync(self, vsync):
        self.make_current()
        if sdl2.SDL_GL_SetSwapInterval(vsync) < 0:
            raise sdl2.ext.SDLError()

    def swap(self):
        self.make_current()
        sdl2.SDL_GL_SwapWindow(self.window)


def create_window(title, width, height, fullscreen=False, borders=True, resizable=True, vsync=True, visible=True):
    flags = sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_ALLOW_HIGHDPI
    if resizable:
        flags |= sdl2.SDL_WINDOW_RESIZABLE
    if fullscreen:
        flags |= sdl2.SDL_WINDOW_FULLSCREEN
    if not borders:
        flags |= sdl2.SDL_WINDOW_BORDERLESS
    if visible:
        flags |= sdl2.SDL_WINDOW_SHOWN
    else:
        flags |= sdl2.SDL_WINDOW_HIDDEN

    window = sdl2.SDL_CreateWindow(title.encode('utf-8'), sdl2.SDL_WINDOWPOS_UNDEFINED, sdl2.SDL_WINDOWPOS_UNDEFINED, width, height, flags)
    if not window:
        raise sdl2.ext.SDLError()

    return Window(window, title, width, height, fullscreen, borders, resizable, vsync)

def create_gl_context(window, versions):
    # Base OpenGL flags.
    sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, 1)
    sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_FLAGS, sdl2.SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG | sdl2.SDL_GL_CONTEXT_RESET_ISOLATION_FLAG)

    # Try every deduced profile.
    for (profile, major, minor) in versions:
        if (profile, major, minor) in _gl_blacklist:
            continue

        _log.debug('Attempting OpenGL {profile} {major}.{minor} context...', profile=profile, major=major, minor=minor)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_PROFILE_MASK, GL_PROFILE_CONSTANTS[profile])
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, major)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, minor)

        context = sdl2.SDL_GL_CreateContext(window.handle)
        if context:
            # Found a working context.
            break

        # Don't try this combo again.
        _gl_blacklist.add((profile, major, minor))
    else:
        raise RuntimeError('Could not create appropriate GL context.')

    context = Context(window.handle, context, profile, major, minor)
    gl_window = _gl.create_gl_window(window, context)
    window.enable_gl(context, gl_window)


## Internals.

_log = rave.log.get(__name__)
_gl = None
_gl_blacklist = set()
