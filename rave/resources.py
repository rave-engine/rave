"""
rave resource manager.

Resource loaders can register themselves with the ResourceManager using register_loader().
Loaders registered should take the following API:
 - loader.can_load(path, obj): Figure out if the given file object (a rave.filesystem.File instance) is fit to be loaded. Seeking/reading allowed.
 - loader.load(path, obj): Decode the given file object. Must return either ImageData, AudioData, or Renderable. ImageData and AudioData instances
     will be passed to create_drawable()/create_soundable() of the current video/audio backends.
"""
import os
import re
import rave.filesystem
import rave.rendering
import rave.backends


## API.

class LoadFailure(Exception):
    """ A failure that occurred while trying to load a resource. """
    def __init__(self, path, errors):
        self.path = path
        self.errors = errors
        self.last_error = errors[-1] if errors else None

    def __str__(self):
        if self.errors:
            reason = 'No loaders found.'
        else:
            reason = '\n' + '\n'.join(str(e) for e in self.errors)
        return '{}.{}: Failed to load resource {path}: {reason}'.format(__name__, self.__class__.__name__, path=self.path, reason=reason)


class ImageData:
    """ Abstract class to hold decoded image data. """
    __slots__ = ('width', 'height', 'pixel_format')

    def __init__(self, width, height, pixel_format=rave.rendering.PixelFormat.FORMAT_RGBA8888):
        self.width = width
        self.height = height
        self.pixel_format = pixel_format

    def get_data(self, amount=None):
        raise NotImplementedError()

class AudioData:
    """ Abstract class to hold decoded audio data. """
    __slots__ = ('channels', 'sample_rate', 'bit_depth', 'streaming')

    def __init__(self, channels=2, sample_rate=44100, bit_depth=16, streaming=False):
        self.channels = channels
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth
        self.streaming = streaming

    def get_data(self, amount=None):
        raise NotImplementedError()


class ResourceManager:
    """ Resource manager. Manages a game's loaders and resource loading. """

    def __init__(self):
        self.loaders = {}

    def load(self, path):
        loaders = []
        for pattern, candidates in self.loaders.items():
            if pattern and not pattern.search(path):
                continue
            loaders.extend(candidates)

        handle = rave.filesystem.open(path, 'rb')
        res, success = self.try_load(path, handle, loaders)
        if not success:
            raise LoadFailure(path, res)

        if isinstance(res, ImageData):
            return rave.backends.get(rave.backends.BACKEND_VIDEO).create_drawable(res)
        if isinstance(res, AudioData):
            return rave.backends.get(rave.backends.BACKEND_AUDIO).create_soundable(res)
        return res

    def try_load(self, path, file, loaders):
        errs = []

        for loader in loaders:
            try:
                file.seek(0, os.SEEK_SET)
            except rave.filesystem.FileNotSeekable:
                pass
            if loader.can_load(path, file):
                try:
                    return loader.load(path, file), True
                except Exception as e:
                    errs.append(e)

        return errs, False

    def register_loader(self, loader, pattern=None):
        if pattern:
            pattern = re.compile(pattern, re.UNICODE)

        self.loaders.setdefault(pattern, [])
        self.loaders[pattern].append(loader)

    def deregister_loader(self, loader, pattern=None):
        if pattern:
            pattern = re.compile(pattern, re.UNICODE)

        self.loaders[pattern].remove(loader)


## Stateful API.

def current():
    import rave.game
    return rave.game.current().resources

def load(path):
    return current().load(path)

def register_loader(loader, pattern=None):
    return current().load(loader, pattern=pattern)

def deregister_loader(loader, pattern=None):
    return current().load(loader, pattern=pattern)
