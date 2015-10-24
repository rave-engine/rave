"""
rave input backend using the SDL2 library.
"""
import sys
import sdl2

import rave.log
import rave.events
import rave.backends
from ..common import events_for
from . import keyboard, mouse, touch, controller

BACKEND_PRIORITY = 50


## Module API.

def load():
    rave.backends.register(rave.backends.BACKEND_INPUT, sys.modules[__name__])

def unload():
    rave.backends.remove(rave.backends.BACKEND_INPUT, sys.modules[__name__])
    sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_HAPTIC | sdl2.SDL_INIT_GAMECONTROLLER)

def backend_load(category):
    if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_HAPTIC | sdl2.SDL_INIT_GAMECONTROLLER) != 0:
        return False
    return True


## Backend API.

def handle_events():
    for ev in events_for('input'):
        if keyboard.handle_event(ev):
            pass
        elif mouse.handle_event(ev):
            pass
        elif touch.handle_event(ev):
            pass
        elif controller.handle_event(ev):
            pass
        else:
            _log.debug('Unknown input event ID: {}', ev.type)

    rave.events.emit('input.dispatch')


## Internal API.

_log = rave.log.get(__name__)
