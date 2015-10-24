"""
Support for decoding audio formats using SDL2_mixer.
"""
import sdl2
import sdl2.ext
import sdl2.sdlmixer as sdl2mixer

import rave.log
import rave.events
import rave.resources

from .common import fs_to_rwops


## Constants.

FORMAT_NAMES = {
    sdl2mixer.MIX_INIT_FLAC: 'FLAC',
    sdl2mixer.MIX_INIT_MOD: '.mod',
    sdl2mixer.MIX_INIT_MODPLUG: 'ModPlug',
    sdl2mixer.MIX_INIT_MP3: 'MP3',
    sdl2mixer.MIX_INIT_OGG: 'OGG Vorbis',
    sdl2mixer.MIX_INIT_FLUIDSYNTH: 'MIDI'
}

FORMAT_PATTERNS = {
    sdl2mixer.MIX_INIT_FLAC: '\.flac$',
    sdl2mixer.MIX_INIT_MOD: '\.mod$',
    sdl2mixer.MIX_INIT_MODPLUG: '\.(mod|s3(m|g?z|r)|xm(g?z|r)?|it(g?z|r)?|am[fs]|dbm|dmf|dsm|far|mdl|med|mtm|okt|ptm|stm|ult|umx|mt2|psm|md(g?z|r)|pat|midi?)$',
    sdl2mixer.MIX_INIT_MP3: '\.mp3$',
    sdl2mixer.MIX_INIT_OGG: '\.ogg$',
    sdl2mixer.MIX_INIT_FLUIDSYNTH: '\.midi?$'
}


## Module API.

def load():
    global _formats
    _formats = sdl2mixer.Mix_Init(sum(FORMAT_NAMES))
    rave.events.hook('engine.new_game', new_game)

def unload():
    sdl2mixer.Mix_Quit()


## Module stuff.

def new_game(event, game):
    for fmt, pattern in FORMAT_PATTERNS.items():
        if _formats & fmt:
            game.resources.register_loader(AudioLoader, pattern)
            _log.debug('Loaded support for {fmt} audio.', fmt=FORMAT_NAMES[fmt])
        else:
            _log.warn('Failed to load support for {fmt} audio.', fmt=FORMAT_NAMES[fmt])


class AudioData(rave.resources.AudioData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_data(self, amount=None):
        pass

class AudioLoader:
    @classmethod
    def can_load(self, path, fd):
        return True

    @classmethod
    def load(self, path, fd):
        handle = fs_to_rwops(fd)
        music = sdl2mixer.Mix_LoadMUS_RW(handle, True)
        if not music:
            raise sdl2.ext.SDLError()

        # or some shit.


## Internals.

_log = rave.log.get(__name__)
_formats = 0
