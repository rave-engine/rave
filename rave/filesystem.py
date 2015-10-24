# rave's virtual file system.
import os
import io
import re
import threading
import collections

import rave.common
import rave.log

# Various standard mount points.
ENGINE_MOUNT = '/.rave'
MODULE_MOUNT = '/.modules'
GAME_MOUNT = '/'
COMMON_MOUNT = '/.common'

## Errors.

class FileSystemError(rave.common.raveError, IOError):
    def __init__(self, filename, message=None):
        super().__init__(message or filename)
        self.filename = filename

class NativeError(FileSystemError):
    def __init__(self, filename, parent):
        super().__init__(filename, message=repr(parent))
        self.native_error = parent

class FileNotFound(FileSystemError, FileNotFoundError):
    pass
class AccessDenied(FileSystemError, PermissionError):
    pass
class FileNotReadable(FileSystemError, PermissionError, io.UnsupportedOperation):
    pass
class FileNotWritable(FileSystemError, PermissionError, io.UnsupportedOperation):
    pass
class FileNotSeekable(FileSystemError, PermissionError, io.UnsupportedOperation):
    pass
class FileClosed(FileSystemError, BrokenPipeError):
    pass
class NotAFile(FileSystemError, IsADirectoryError):
    pass
class NotADirectory(FileSystemError, NotADirectoryError):
    pass


## API.

class FileSystem:
    # Canonical path separator.
    PATH_SEPARATOR = '/'
    # Root.
    ROOT = '/'
    # Unnormalized path pattern.
    BAD_PATH_PATTERN = re.compile(r'(?:{0}{{2,}}|(?:{0}|^)\.+(?:{0}|$))'.format(PATH_SEPARATOR))

    def __init__(self):
        # Lock when rebuilding cache or modifying the file system.
        self._lock = threading.RLock()
        # Clear the file system.
        self.clear()

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def clear(self):
        if hasattr(self, '_roots'):
            _log.trace('Clearing file system...')

        with self._lock:
            # File system roots. A mapping of path -> [ list of providers ].
            self._roots = {}
            # Transforming providers. A mapping of extension -> [ list of providers ].
            self._transformers = {}
            # File/directory list cache. A mapping of filename -> [ list of providers ].
            self._file_cache = None
            # Directory content cache. A mapping of directory -> { set of direct contents }.
            self._listing_cache = None


    ## Building file cache.

    def _build_cache(self):
        """ Rebuild internal file cache. This will make looking up files, errors notwithstanding, an O(1) lookup operation. """
        _log.trace('Building cache...')

        with self._lock:
            self._file_cache = { self.ROOT: [] }
            self._listing_cache = { self.ROOT: set() }

            for root, providers in self._roots.items():
                for provider in providers:
                    self._build_provider_cache(provider, root)

    def _build_provider_cache(self, provider, root):
        """
        Add provider to file cache. This will traverse the providers file and iteratively add them to the file cache.
        This function will check if transformers exist for the file in the process, which might indirectly trigger recursion,
        since a transformed file acts as a new provider.
        """
        _log.trace('Caching mount point {root} <- {prov}...', prov=provider, root=root)
        # Add root to cache.
        self._cache_directory(provider, root, root)

        # Traverse provider and add files and directories on the go.
        for subpath in provider.list():
            path = self.join(root, subpath)

            if provider.isdir(subpath):
                self._cache_directory(provider, root, path)
            else:
                self._cache_file(provider, root, path)

    def _build_transformer_cache(self, transformer, pattern):
        """
        Add `transformer` to file cache. This will search all existing files to look for files that match the `pattern`, and if so,
        adds the transformer as a new provider for that file and optionally removes it if the transformer consumes the file.
        """
        _log.trace('Caching {trans} for {pattern}...', trans=transformer, pattern=pattern.pattern)

        # Traverse paths to find matching files.
        for file in self._file_cache.copy():
            if not pattern.search(file):
                continue

            # Gotcha.
            try:
                handle = self.open(file)
            except:
                _log.warn('Couldn\'t open {path} for transformer {transformer}. Moving on...'.format(path=file, transformer=transformer))
                continue
            self._cache_transformed_file(transformer, file, handle)

    def _cache_directory(self, provider, root, path):
        """ Add `path`, provided by `provider`, as a directory to the file cache. """
        _log.trace('Caching directory: {path} <- {provider}...', path=path, provider=provider)

        with self._lock:
            self._listing_cache.setdefault(path, set())
        self._cache_entry(provider, root, path)

    def _cache_file(self, provider, root, path):
        """ Add `path`, provided by `provider`, as a file to the file cache. """
        _log.trace('Caching file: {path} <- {provider}...', path=path, provider=provider)
        localpath = self._local_file(root, path)

        for pattern, transformers in self._transformers.items():
            if not pattern.search(path):
                continue

            consumed = False
            for transformer in transformers:
                try:
                    handle = provider.open(localpath)
                except Exception as e:
                    _log.warn('Couldn\'t open {provider}:{path} for transformer {transformer}. Error: {err}',
                              provider=provider, path=localpath, transformer=transformer, err=e)
                    continue

                consumed = self._cache_transformed_file(transformer, path, handle)
                if consumed:
                    break

            # Stop processing entirely if we have consumed the file.
            if consumed:
                _log.debug('Cached file {path} consumed by transformer.', path=path)
                break
        else:
            # No transformers found for file, or file wasn't consumed. Add it to cache.
            self._cache_entry(provider, root, path)

    def _cache_entry(self, provider, root, path):
        """ Add an entry at `path`, provided by `provider`, to the file cache. """
        with self._lock:
            self._file_cache.setdefault(path, [])
            if provider and provider not in self._file_cache[path]:
                self._file_cache[path].append((provider, root))

            if path != self.ROOT:
                parent = self.dirname(path)
                if not self.exists(parent):
                    self._cache_directory(None, None, parent)

                basename = self.basename(path)
                self._listing_cache.setdefault(parent, set())
                self._listing_cache[parent].add(basename)

    def _cache_transformed_file(self, transformer, path, handle):
        """
        Add a transformed file at `path`, transformed by `transformer`, to the file cache.
        This will return whether or not the original file was consumed by `transformer`.
        It might fail to add the transformed file to the file cache if the transformers raises an error.

        If the transformer consumes the original file, this function will remove the original file from the file system,
        if it exists on it.
        """
        try:
            instance = transformer(path, handle)
        except Exception as e:
            _log.warn('Error while transforming {path} with {transformer}: {err}', path=path, transformer=transformer, err=e)
            return False

        if not instance.valid():
            return False
        _log.trace('Caching transformed file: {path} <- {trans}...', path=path, trans=transformer)

        # Determine root directory of files.
        if instance.relative():
            parentdir = self.dirname(path)
        else:
            parentdir = self.ROOT

        # Mount as provider.
        self._build_provider_cache(instance, parentdir)

        if instance.consumes():
            # Remove file cache for now-consumed file.
            with self._lock:
                if path in self._file_cache:
                    del self._file_cache[path]
            return True
        else:
            return False

    def _providers_for_file(self, path):
        """
        Return a generator yielding (provider, mountpoint) tuples for all providers that provide given `path`.
        Priority is done on a last-come last-serve basis: the last provider added that provides `path` is yielded first.
        """
        if self._file_cache is None:
            self._build_cache()

        if path not in self._file_cache:
            raise FileNotFound(path)

        for provider, mountpoint in reversed(self._file_cache[path]):
            yield provider, self._local_file(mountpoint, path)

    def _local_file(self, root, path):
        if root == self.ROOT:
            return path
        return path[len(root):]


    ## API.

    def list(self, subdir=None):
        """ List all files and directories in the root file system, or `subdir` if given, recursively. """
        if self._file_cache is None:
            self._build_cache()

        if subdir is not None:
            subdir = self.normalize(subdir)
            if not self.isdir(subdir):
                if not self.exists(subdir):
                    raise FileNotFound(subdir)
                else:
                    raise NotADirectory(subdir)

            files = { '/' }
            to_process = collections.deque()
            to_process.append(subdir)

            while to_process:
                target = to_process.popleft()

                for entry in self._listing_cache[target]:
                    path = self.join(target, entry)
                    if self.isdir(path):
                        to_process.append(path)
                    files.add(path.replace(subdir, ''))

            return files
        else:
            return set(self._file_cache)

    def listdir(self, subdir=None):
        """ List all files and directories in the root file system, or `subdir` is given. """
        if self._file_cache is None:
            self._build_cache()

        if subdir is None:
            subdir = self.ROOT
        else:
            subdir = self.normalize(subdir)
            if not self.isdir(subdir):
                if not self.exists(subdir):
                    raise FileNotFound(subdir)
                else:
                    raise NotADirectory(subdir)

        return self._listing_cache[subdir]

    def mount(self, path, provider):
        """
        Mount `provider` at `path` in the virtual file system.

        `provider` must be an object satisfying the following API:
         - list(): return a list of all file names (including folders) this provider can provide.
         - has(filename): return whether this provider can open given file.
         - open(filename, **kwargs): open a file, has to raise one of the subclasses of `FileSystemError` on error, else return a subclass of `File`.
         - isfile(filename): check if the given file is a file, should raise applicable `FileSystemError` subclass if applicable,
             except for NotAFile/NotADirectory, or return a boolean.
         - isdir(filename): check if the given file is a directory, should raise applicable `FileSystemError` subclass if applicable,
             except for NotAFile/NotADirectory, or return a boolean.

        A path or file can be provided by different providers. Their file lists will be merged.
        Conflicting files will be handled as such:
         - The last provider that has been mounted will serve the file first.
         - If an error occurs while serving the file, the next provider according to these rules will serve it.
        """
        path = self.normalize(path)
        with self._lock:
            self._roots.setdefault(path, [])
            self._roots[path].append(provider)

        _log.debug('Mounted {provider} on {path}.', provider=provider, path=path)
        if self._file_cache is None:
            self._build_cache()
        else:
            self._build_provider_cache(provider, path)

    def unmount(self, path, provider):
        """ Unmount `provider` from `path` in the virtual file system. Will trigger a full cache rebuild. """
        path = self.normalize(path)
        with self._lock:
            self._roots[path].remove(provider)

        _log.debug('Unmounted {provider} from {path}.', provider=provider, path=path)
        self._build_cache()

    def transform(self, pattern, transformer):
        """
        TRANSFORMERS! TRANSFORMERS! MORE THAN MEETS THE EYE! TRANSFORMERS!
        Add `transformer` as a transformer for files matching `pattern`.

        `transformer` has to be a class(!) satisfying the provider API (see `mount`), plus the following API:
         - __init__(filename, handle): initialize object, can raise any kind of error if the file is invalid.
           `handle` is a `File` object pointing to the opened file.
         - valid(): return whether the file is valid according to the format this transformer parses.
         - consumes(): return whether the source file should be retained in the file system.
         - relative(): return whether files exposed by this transformer should be relative to the path of the source file or absolute.
        """
        pattern = re.compile(pattern, re.UNICODE)

        with self._lock:
            self._transformers.setdefault(pattern, [])
            self._transformers[pattern].append(transformer)

        _log.debug('Added transformer {transformer} for pattern {pattern}.', transformer=transformer, pattern=pattern.pattern)
        if self._file_cache is None:
            self._build_cache()
        else:
            self._build_transformer_cache(transformer, pattern)

    def untransform(self, pattern, transformer):
        """ Remove a transformer from the virtual file system. Will trigger a full cache rebuild. """
        pattern = re.compile(pattern, re.UNICODE)

        with self._lock:
            self._transformers[pattern].remove(transformer)

        _log.debug('Removed transformer {transformer} for pattern {pattern}.', transformer=transformer, pattern=pattern.pattern)
        self._build_cache()

    def open(self, filename, *args, **kwargs):
        """
        Open `filename` and return a corresponding `File` object. Will raise `FileNotFound` if the file was not found.
        Will only raise the error from the last attempted provider if multiple providers raise an error.
        """
        error = None

        filename = self.normalize(filename)
        if self.isdir(filename):
            raise NotAFile(filename)

        for provider, localfile in self._providers_for_file(filename):
            try:
                _log.trace('Opening {filename} from {provider}...', filename=filename, provider=provider)
                return provider.open(localfile, *args, **kwargs)
            except FileNotFound:
                continue
            except FileSystemError as e:
                error = e

        if error:
            raise error
        else:
            raise FileNotFound(filename)

    def exists(self, filename):
        """ Return whether or not `filename` exists. """
        if self._file_cache is None:
            self._build_cache()

        filename = self.normalize(filename)
        return filename in self._file_cache

    def isdir(self, filename):
        """ Return whether or not `filename` exists and is a directory. """
        if self._file_cache is None:
            self._build_cache()

        filename = self.normalize(filename)
        return filename in self._listing_cache

    def isfile(self, filename):
        """ Return whether or not `filename` exists and is a file. """
        if self._file_cache is None:
            self._build_cache()

        filename = self.normalize(filename)
        return filename in self._file_cache and filename not in self._listing_cache

    def dirname(self, path):
        """ Return the directory part of the given `path`. """
        path = self.normalize(path)
        return path.rsplit(self.PATH_SEPARATOR, 1)[0] or self.ROOT

    def basename(self, path):
        """ Return the filename part of the given `path`. """
        if path == self.ROOT:
            return ''
        path = self.normalize(path)
        return path.rsplit(self.PATH_SEPARATOR, 1)[1]

    def join(self, *paths, normalized=True):
        """ Join path components into a file system path. Optionally normalize the result. """
        if normalized:
            return self.normalize(self.PATH_SEPARATOR.join(paths))
        return self.PATH_SEPARATOR.join(paths)

    def split(self, path, *args, **kwargs):
        """ Split path by path separator. """
        return path.split(self.PATH_SEPARATOR, *args, **kwargs)

    def normalize(self, path):
        """ Normalize path to canonical path. """
        # Quick check to see if we need to normalize at all.
        if path.startswith(self.ROOT) and not self.BAD_PATH_PATTERN.search(path):
            if path.endswith(self.PATH_SEPARATOR) and path != self.ROOT:
                return path[:-len(self.PATH_SEPARATOR)]
            return path

        # Remove root.
        if path.startswith(self.ROOT):
            path = path[len(self.ROOT):]

        # Split path into directory pieces and remove empty or redundant directories.
        pieces = [ piece for piece in self.split(path) if piece and piece != '.' ]
        # Remove parent directory entries.
        while '..' in pieces:
            i = pieces.index('..')
            del pieces[i]
            # The preceding directory too, of course.
            if i > 0:
                del pieces[i - 1]

        return self.ROOT + self.join(*pieces, normalized=False)


class File(io.IOBase):
    """
    An open file in the virtual file system.
    Subclasses are expected to at least override the following:
     - opened()
     - readable() (if readable, returns False by default)
     - writable() (if writable, returns False by default)
     - seekable() (if seekable, returns False by default)
     - close()
     - read(amount=None) (if readable, raises FileNotReadable by default)
     - write(data) (if writable, raises FileNotWritable by default)
     - seek(position, mode) (if seekable, raises FileNotSeekable by default)
     - tell() (if seekable, raises FileNotSeekable by default)
    """
    def __del__(self):
        try:
            self.close()
        except:
            # Nothing we can do about it now, anyway.
            pass

    def close(self):
        """ Close file. Any operation on the file after calling this method will fail with `FileClosed` raised. """
        raise NotImplementedError

    def opened(self):
        """ Return whether this file is open. """
        raise NotImplementedError

    def readable(self):
        """ Return whether this file is readable. """
        return False

    def writable(self):
        """ Return whether this file is writable. """
        return False

    def seekable(self):
        """ Return whether this file is seeekable. """
        return False

    def read(self, amount=None):
        """ Read `amount` bytes from file. Will read full contents if `amount` is not given. """
        raise FileNotReadable(self)

    def write(self, data):
        """ Write `data` to file. """
        raise FileNotWritable(self)

    def seek(self, position, mode=os.SEEK_CUR):
        """ Seek in file. May raise `FileNotSeekable` if this file can't be seeked in. """
        raise FileNotSeekable(self)

    def tell(self):
        """ Tell current file position. May raise `FileNotSeekable` if this file can't be seeked in. """
        raise FileNotSeekable(self)


class FileSystemProvider:
    """ A provider to mount a filesystem within another filesystem. """
    def __init__(self, fs):
        self.fs = fs

    def __repr__(self):
        return '<FileSystemProvider: {}>'.format(self.fs)

    def list(self):
        return self.fs.list()

    def open(self, filename, *args, **kwargs):
        return self.fs.open(filename, *args, **kwargs)

    def has(self, filename):
        return self.fs.isfile(filename)

    def isfile(self, filename):
        return self.fs.isfile(filename)

    def isdir(self, filename):
        return self.fs.isdir(filename)


## Stateful API.

def current():
    import rave.game, rave.engine
    game = rave.game.current()
    if not game:
        return rave.engine.engine.fs
    return game.fs

def list(subdir=None):
    return current().list(subdir)

def listdir(subdir=None):
    return current().listdir(subdir)

def mount(path, provider):
    return current().mount(path, provider)

def unmount(path, provider):
    return current().unmount(path, provider)

def transform(pattern, transformer):
    return current().transform(pattern, transformer)

def untransform(pattern, transformer):
    return current().untransform(pattern, transformer)

def open(filename, *args, **kwargs):
    return current().open(filename, *args, **kwargs)

def exists(filename):
    return current().exists(filename)

def isfile(filename):
    return current().isfile(filename)

def isdir(filename):
    return current().isdir(filename)

def dirname(path):
    return current().dirname(path)

def basename(path):
    return current().basename(path)

def join(*paths, normalized=True):
    return current().join(*paths, normalized=normalized)

def split(path, *args, **kwargs):
    return current().split(path, *args, **kwargs)

def normalize(path):
    return current().normalize(path)


## Internals.

_log = rave.log.get(__name__)

