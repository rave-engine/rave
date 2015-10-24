"""
Support for decoding image formats using SDL2_Image.
"""
import sdl2
import sdl2.ext
import sdl2.sdlimage as sdl2image

import rave.log
import rave.events
import rave.rendering
import rave.resources

from .common import fs_to_rwops


## Constants.

FORMAT_NAMES = {
    sdl2image.IMG_INIT_JPG:  'JPEG',
    sdl2image.IMG_INIT_PNG:  'PNG',
    sdl2image.IMG_INIT_TIF:  'TIFF',
    sdl2image.IMG_INIT_WEBP: 'WebP'
}
FORMAT_PATTERNS = {
    sdl2image.IMG_INIT_JPG: '.jpe?g$',
    sdl2image.IMG_INIT_PNG: '.png$',
    sdl2image.IMG_INIT_TIF: '.tiff?$',
    sdl2image.IMG_INIT_WEBP: '.webp$'
}


## Module API.

def load():
    global _formats
    _formats = sdl2image.IMG_Init(sum(FORMAT_NAMES))
    rave.events.hook('engine.new_game', new_game)

def unload():
    sdl2image.IMG_Quit()


## Module stuff.

def new_game(event, game):
    for fmt, pattern in FORMAT_PATTERNS.items():
        if _formats & fmt:
            game.resources.register_loader(ImageLoader, pattern)
            _log.debug('Loaded support for {fmt} images.', fmt=FORMAT_NAMES[fmt])
        else:
            _log.warn('Failed to load support for {fmt} images.', fmt=FORMAT_NAMES[fmt])


class ImageData(rave.resources.ImageData):
    __slots__ = ('surface',)

    def __init__(self, surface, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.surface = surface

    def __del__(self):
        sdl2.SDL_FreeSurface(self.surface)

    def get_data(self, amount=None):
        if amount:
            return self.surface.contents.pixels[:amount]
        return self.surface.contents.pixels

class ImageLoader:
    @classmethod
    def can_load(cls, path, fd):
        return True

    @classmethod
    def load(cls, path, fd):
        handle = fs_to_rwops(fd)
        surface = sdl2image.IMG_Load_RW(handle, True)
        if not surface:
            raise sdl2.ext.SDLError()

        pixfmt = sdl2.SDL_AllocFormat(sdl2.SDL_PIXELFORMAT_BGRA8888)
        converted = sdl2.SDL_ConvertSurface(surface, pixfmt, 0)
        sdl2.SDL_FreeFormat(pixfmt)
        sdl2.SDL_FreeSurface(surface)
        if not converted:
            raise sdl2.ext.SDLError()

        return ImageData(converted, converted.contents.w, converted.contents.h, rave.rendering.PixelFormat.FORMAT_BGRA8888)


## Internals.

_log = rave.log.get(__name__)
_formats = 0
