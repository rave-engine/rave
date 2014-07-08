"""
rave file system provider module.

This module provides a source for rave's virtual file system that sources from a real existing file system.
"""
import os
from os import path
import builtins
import errno
from functools import wraps
import rave.filesystem as fs

__author__ = 'Shiz'
__version__ = '0.1.0'
__version_info__ = (0, 1, 0)
__license__ = '2-clause BSD'



## Internal module stuff.

def _is_error(self, exception, *errors):
    """ Determine if an exception belongs to one of the given named errno module errors. """
    errors = [ getattr(errno, error, None) for error in errors ]
    return exception.errno in errors

def _translate_errors(f):
    """ Translate native errors to rave file system errors. """
    @wraps(f)
    def translate(self, *args, **kwargs):
        filename = None
        # Kind of dirty.
        if isinstance(self, FileSystemFile):
            filename = self.filename
        elif isinstance(self, FileSystemSource):
            filename = self.basepath

        try:
            return f(self, *args, **kwargs)
        except fs.FileSystemError:
            raise
        except FileNotFoundError as e:
            raise fs.FileNotFound(filename) from e
        except PermissionError as e:
            raise fs.AccessDenied(filename) from e
        except IsADirectoryError as e:
            raise fs.NotAFile(filename) from e
        except NotADirectoryError as e:
            raise fs.NotADirectory(filename) from e
        except IOError as e:
            # Translate errno errors.
            if _is_error(e, 'EPERM', 'EACCES', 'EFAULT', 'EBUSY'):
                raise fs.AccessDenied(filename) from e
            if _is_error(e, 'ENOENT', 'ENXIO', 'ENODEV'):
                raise fs.FileNotFound(filename) from e
            if _is_error(e, 'ENOTDIR'):
                raise fs.NotADirectory(filename) from e
            if _is_error(e, 'EISDIR'):
                raise fs.NotAFile(filename) from e
            if _is_error(e, 'EROFS'):
                raise fs.FileNotWritable(filename) from e
            # We have no clue, raise a native error.
            raise fs.NativeError(filename, e) from e

    return translate

def _ensure_opened(f):
    """ Check if file is open before doing anything. """
    @wraps(f)
    def check(self, *args, **kwargs):
        if not self.opened():
            raise fs.FileClosed(self.filename)
        return f(self, *args, **kwargs)

    return check


class FileSystemSource:
    """ A provider that sources from an actual underlying file system. """

    def __init__(self, filesystem, basepath):
        self.filesystem = filesystem
        self.basepath = path.abspath(basepath)
        self._file_list = None

        if not path.exists(self.basepath):
            raise fs.FileNotFound(self.basepath)
        elif not path.isdir(self.basepath):
            raise fs.NotADirectory(self.basepath)
        elif not os.access(self.basepath, os.R_OK | os.X_OK):
            raise fs.FileNotReadable(self.basepath)

    def __repr__(self):
        return '<{cls}: {base}>'.format(cls=self.__class__.__name__, base=self.basepath)

    def _to_native_path(self, filename):
        """ Translate virtual file system path to native file system path. """
        filename = filename.lstrip(self.filesystem.PATH_SEPARATOR).replace(self.filesystem.PATH_SEPARATOR, os.sep)
        return path.join(self.basepath, filename)

    def _from_native_path(self, filename):
        """ Translate native file system path to virtual file system path. """
        filename = path.relpath(filename, self.basepath)
        return filename.replace(os.sep, self.filesystem.PATH_SEPARATOR)

    @_translate_errors
    def _build_file_list(self):
        """ Build file list from os.walk. """
        self._file_list = []

        for basepath, directories, files in os.walk(self.basepath):
            self._file_list.extend(self._from_native_path(path.join(basepath, directory)) for directory in directories)
            self._file_list.extend(self._from_native_path(path.join(basepath, file)) for file in files)

    def list(self):
        if not self._file_list:
            self._build_file_list()

        return self._file_list

    def has(self, filename):
        return path.exists(self._to_native_path(filename))

    def isfile(self, filename):
        if not self.has(filename):
            raise fs.FileNotFound(filename)
        return path.isfile(self._to_native_path(filename))

    def isdir(self, filename):
        if not self.has(filename):
            raise fs.FileNotFound(filename)
        return path.isdir(self._to_native_path(filename))

    def open(self, filename, **kwargs):
        if not self.has(filename):
            raise fs.FileNotFound(filename)
        if not self.isfile(filename):
            raise fs.NotAFile(filename)

        native_path = self._to_native_path(filename)
        return FileSystemFile(self.filesystem, native_path, **kwargs)


class FileSystemFile(fs.File):
    """ A file on the actual file system. """

    def __init__(self, filesystem, filename, **kwargs):
        self.filesystem = filesystem
        self.filename = filename
        self._handle = None
        self._readable = None
        self._writable = None
        self._seekable = None
        self._open(**kwargs)

    def __repr__(self):
        return '<{cls}[{file}]>'.format(cls=self.__class__.__name__, file=self.filename)

    @_translate_errors
    def _open(self, **kwargs):
        self._handle = builtins.open(self.filename, 'rb+', **kwargs)

    @_translate_errors
    def _in_mode(self, *modes):
        return any(mode in self._handle.mode for mode in modes)

    @_translate_errors
    def close(self):
        if self.opened():
            self._handle.close()
            self._handle = None

    def opened(self):
        return self._handle is not None

    @_translate_errors
    @_ensure_opened
    def readable(self):
        if self._readable is None:
            self._readable = os.access(self.filename, os.R_OK) and self._in_mode('r', 'w+', 'a+')
        return self._readable

    @_translate_errors
    @_ensure_opened
    def writable(self):
        if self._writable is None:
            self._writable = os.access(self.filename, os.W_OK) and self._in_mode('w', 'a', 'r+')
        return self._writable

    @_ensure_opened
    def seekable(self):
        if self._seekable is None:
            try:
                self._handle.seek(0, os.SEEK_CUR)
            except:
                self._seekable = False
            else:
                self._seekable = True
        return self._seekable

    @_translate_errors
    @_ensure_opened
    def read(self, amount=None):
        if not self.readable():
            raise fs.FileNotReadable(self.filename)
        return self._handle.read(amount)

    @_translate_errors
    @_ensure_opened
    def write(self, data):
        if not self.writable():
            raise fs.FileNotWritable(self.filename)
        self._handle.write(data)

    @_translate_errors
    @_ensure_opened
    def seek(self, amount, relative=True):
        if not self.seekable():
            raise fs.FileNotSeekable(self.filename)

        if relative:
            self._handle.seek(amount, os.SEEK_CUR)
        else:
            self._handle.seek(amount, os.SEEK_SET)
        return self.tell()

    @_translate_errors
    @_ensure_opened
    def tell(self):
        if not self.seekable():
            raise fs.FileNotSeekable(self.filename)
        return self._handle.tell()
