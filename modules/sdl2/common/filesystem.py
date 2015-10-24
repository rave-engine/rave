"""
SDL_RWops wrappers for rave's virtual filesystem files.
"""
import os
import sdl2
import rave.filesystem


## API.

def rwops_open(filename):
    handle = rave.filesystem.open(filename)
    return fs_to_rwops(handle)

def fs_to_rwops(handle):
    return sdl2.rw_from_object(RWOpsWrapper(handle))


## Wrapper.

class RWOpsWrapper:
    """ A class that wraps rave.filesystem.File operations into an SDL_RWOps compatible API. """
    __slots__ = ('handle',)

    def __init__(self, handle):
        self.handle = handle

    def read(self, length):
        data = self.handle.read(length)
        if len(data) != length:
            raise ValueError('Not enough data available.')
        return data

    def write(self, data):
        return self.handle.write(data)

    def seek(self, offset, whence):
        if whence == sdl2.RW_SEEK_SET:
            mode = os.SEEK_SET
        elif whence == sdl2.RW_SEEK_CUR:
            mode = os.SEEK_CUR
        elif whence == sdl2.RW_SEEK_END:
            mode = os.SEEK_END
        else:
            raise ValueError('Unknown seek mode.')
        return self.handle.seek(offset, mode)

    def tell(self):
        return self.handle.tell()

    def close(self):
        return self.handle.close()
