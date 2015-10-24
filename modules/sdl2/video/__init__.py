"""
rave video backend using the SDL2 library and OpenGL.
"""
import sdl2

from . import events, window

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
handle_events = events.handle_events