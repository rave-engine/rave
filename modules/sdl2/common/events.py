"""
Wrapper for SDL2 events.
"""
from ctypes import byref
import sdl2
import rave.log
import rave.events


EVENT_SUBSYSTEMS = {
    sdl2.SDL_QUIT:                      'system',
    sdl2.SDL_APP_TERMINATING:           'system',
    sdl2.SDL_APP_LOWMEMORY:             'system',
    sdl2.SDL_APP_WILLENTERBACKGROUND:   'system',
    sdl2.SDL_APP_DIDENTERBACKGROUND:    'system',
    sdl2.SDL_APP_WILLENTERFOREGROUND:   'system',
    sdl2.SDL_APP_DIDENTERFOREGROUND:    'system',

    sdl2.SDL_WINDOWEVENT:               'video',
    sdl2.SDL_SYSWMEVENT:                'video',

    sdl2.SDL_KEYDOWN:                   'input',
    sdl2.SDL_KEYUP:                     'input',
    sdl2.SDL_TEXTEDITING:               'input',
    sdl2.SDL_TEXTINPUT:                 'input',

    sdl2.SDL_MOUSEMOTION:               'input',
    sdl2.SDL_MOUSEBUTTONDOWN:           'input',
    sdl2.SDL_MOUSEBUTTONUP:             'input',
    sdl2.SDL_MOUSEWHEEL:                'input',

    sdl2.SDL_JOYAXISMOTION:             'input',
    sdl2.SDL_JOYBALLMOTION:             'input',
    sdl2.SDL_JOYHATMOTION:              'input',
    sdl2.SDL_JOYBUTTONDOWN:             'input',
    sdl2.SDL_JOYBUTTONUP:               'input',
    sdl2.SDL_JOYDEVICEADDED:            'input',
    sdl2.SDL_JOYDEVICEREMOVED:          'input',

    sdl2.SDL_CONTROLLERAXISMOTION:      'input',
    sdl2.SDL_CONTROLLERBUTTONDOWN:      'input',
    sdl2.SDL_CONTROLLERBUTTONUP:        'input',
    sdl2.SDL_CONTROLLERDEVICEADDED:     'input',
    sdl2.SDL_CONTROLLERDEVICEREMOVED:   'input',

    sdl2.SDL_FINGERDOWN:                'input',
    sdl2.SDL_FINGERUP:                  'input',
    sdl2.SDL_FINGERMOTION:              'input',
    sdl2.SDL_DOLLARGESTURE:             'input',
    sdl2.SDL_DOLLARRECORD:              'input',
    sdl2.SDL_MULTIGESTURE:              'input',

    sdl2.SDL_CLIPBOARDUPDATE:           'system',
    sdl2.SDL_DROPFILE:                  'system',

    #sdl2.SDL_AUDIODEVICEADDED:          'audio',
    #sdl2.SDL_AUDIODEVICEREMOVED:        'audio',

    sdl2.SDL_RENDER_TARGETS_RESET:      'video',
    sdl2.SDL_RENDER_DEVICE_RESET:       'video',
}


## API.

def load():
    rave.events.hook('engine.new_game', hook_events)

def hook_events(ev, game):
    game.events.hook('backend.events.start', _start_processing)
    game.events.hook('backend.events.stop', _stop_processing)

def events_for(subsystem):
    """ Get all pending events relevant for a certain subsystem. """
    _pump_events()
    if subsystem in _pending_events:
        return _pending_events.pop(subsystem)
    return []

def handle_events():
    """ Handle system events. """
    for ev in events_for('system'):
        if ev.type == sdl2.SDL_APP_WILLENTERBACKGROUND:
            rave.events.emit('game.suspend')
        elif ev.type == sdl2.SDL_APP_DIDENTERBACKGROUND:
            rave.events.emit('game.suspended')
        elif ev.type == sdl2.SDL_APP_WILLENTERFOREGROUND:
            rave.events.emit('game.resume')
        elif ev.type == sdl2.SDL_APP_DIDENTERFOREGROUND:
            rave.events.emit('game.resumed')


## Internal.

_log = rave.log.get(__name__)
_pending_events = {}
_do_pump = False

def _pump_events():
    """ Get events from SDL and sort them out. """
    global _do_pump
    if not _do_pump:
        return

    while True:
        ev = sdl2.SDL_Event()
        if sdl2.SDL_PollEvent(byref(ev)) == 0:
            break
        if ev.type in EVENT_SUBSYSTEMS:
            subsystem = EVENT_SUBSYSTEMS[ev.type]
        else:
            subsystem = 'unknown'

        _log.trace('Got event {} -> {}.', ev.type, subsystem)
        _pending_events.setdefault(subsystem, [])
        _pending_events[subsystem].append(ev)

    # Don't pump again until next round.
    _do_pump = False

def _start_processing(ev):
    # Enable the pump.
    global _do_pump
    _do_pump = True

def _stop_processing(ev):
    # Disable the pump.
    global _do_pump
    _do_pump = False
