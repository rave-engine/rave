"""
rave audio backend using the SDL2 library.
"""
import sys
import sdl2
import sdl2.ext
import sdl2.sdlmixer as sdl2mixer

import rave.log
import rave.events
import rave.backends
import rave.resources

from ..common import fs_to_rwops
from . import formats

__author__ = 'Shiz'
__provides__ = [ 'audio' ]
BACKEND_PRIORITY = 50


def load():
    rave.backends.register(rave.backends.BACKEND_AUDIO, sys.modules[__name__])

def unload():
    rave.backends.remove(rave.backends.BACKEND_AUDIO, sys.modules[__name__])

def load_backend(category):
    global _formats

    if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_AUDIO) != 0:
        return False

        _formats = sdl2mixer.Mix_Init(sum(formats.FORMAT_NAMES))
        if not _formats:
            return False

    rave.events.hook('engine.new_game', new_game)
    return True

def unload_backend(category):
    sdl2mixer.Mix_Quit()
    sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_AUDIO)

def handle_events():
    pass


## Backend stuff.

def new_game(event, game):
    formats.register_loaders(game.resources)



## Internals.

_log = rave.log.get(__name__)
_formats = 0
