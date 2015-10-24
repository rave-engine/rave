"""
rave video backend using the SDL2 library and OpenGL.
"""
import sdl2
import rave.log
import rave.events

from ..common import events_for, handle_events as handle_system_events
from . import window

__provides__ = [ 'opengl_manager' ]


## API.

def load():
    if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_VIDEO) != 0:
        return False
    return True

def unload():
    sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_VIDEO)


## Video backend API.

create_window = window.create_window
create_gl_context = window.create_gl_context

def handle_events():
    # Handle system events.
    handle_system_events()

    for ev in events_for('video'):
        # Dispatch events.
        if ev.type == sdl2.SDL_WINDOWEVENT:
            window = ev.window.windowID

            if ev.window.event == sdl2.SDL_WINDOWEVENT_SHOWN:
                rave.events.emit('video.window.shown', window)
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_HIDDEN:
                rave.events.emit('video.window.hidden', window)
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_EXPOSED:
                rave.events.emit('video.window.exposed', window)
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_MOVED:
                rave.events.emit('video.window.moved', window, ev.window.data1, ev.window.data2)
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_SIZE_CHANGED:
                # Handled in SDL_WINDOWEVENT_RESIZED.
                pass
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                rave.events.emit('video.window.resized', window, ev.window.data1, ev.window.data2)
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_MINIMIZED:
                rave.events.emit('video.window.minimized', window)
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_MAXIMIZED:
                rave.events.emit('video.window.maximized', window)
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_RESTORED:
                rave.events.emit('video.window.restored', window)
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_ENTER:
                rave.events.emit('video.window.focused', window, 'mouse')
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_LEAVE:
                rave.events.emit('video.window.unfocused', window, 'mouse')
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_FOCUS_GAINED:
                rave.events.emit('video.window.focused', window, 'keyboard')
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_FOCUS_LOST:
                rave.events.emit('video.window.unfocused', window, 'keyboard')
            elif ev.window.event == sdl2.SDL_WINDOWEVENT_CLOSE:
                rave.events.emit('video.window.close', window)
            else:
                _log.warn('Got unknown SDL_WINDOWEVENT of type {}.', ev.window.event)
        elif ev.type == sdl2.SDL_SYSWMEVENT:
            # Nothing for now.
            pass
        elif ev.type == sdl2.SDL_RENDER_TARGETS_RESET:
            # Nothing for now.
            pass
        elif ev.type == sdl2.SDL_RENDER_DEVICE_RESET:
            # Nothing for now.
            pass
        else:
            _log.warn('Got unknown event of type {}.', ev.type)


## Internals.

_log = rave.log.get(__name__)
