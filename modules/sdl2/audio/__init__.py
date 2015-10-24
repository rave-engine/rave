"""
rave audio backend using the SDL2 library.
"""
import sys
import sdl2
import rave.backends

__author__ = 'Shiz'
__provides__ = [ 'audio' ]
BACKEND_PRIORITY = 50


def load():
    rave.backends.register(rave.backends.BACKEND_AUDIO, sys.modules[__name__])

def load_backend(category):
    if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_AUDIO) != 0:
        return False
    return True

def handle_events():
    pass

def unload():
    rave.backends.remove(rave.backends.BACKEND_AUDIO, sys.modules[__name__])
    sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_AUDIO)
