# rave's virtual file system.
import builtins
import re
import threading

from rave import common, log


## Errors.

class FileSystemError(common.raveError, IOError):
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
class FileNotReadable(FileSystemError, PermissionError):
    pass
class FileNotWritable(FileSystemError, PermissionError):
    pass
class FileNotSeekable(FileSystemError, PermissionError):
    pass
class FileClosed(FileSystemError, BrokenPipeError):
    pass
class NotAFile(FileSystemError, IsADirectoryError):
    pass
class NotADirectory(FileSystemError, NotADirectoryError):
    pass


## Internals.

_log = log.get(__name__)


## API.

class FileSystem:
    # Canonical path separator.
    PATH_SEPARATOR = '/'
    # Root.
    ROOT = '/'
    # Unnormalized path pattern.
    BAD_PATH_PATTERN = re.compile(r'{0}\.*{0}'.format(PATH_SEPARATOR))

    def __init__(self):
        # Lock when rebuilding cache or modifying the file system.
        self._lock = threading.RLock()
        # Clear the file system.
        self.clear()

    def clear(self):
        with self._lock:
            # File system roots. A mapping of path -> [ list of providers ].
            self._roots = {}
            # On-demand providers. A list of providers.
            self._on_demands = []
            # Transforming providers. A mapping of extension -> [ list of providers ].
            self._transformers = {}

            # File/directory list cache. A mapping of filename -> [ list of providers ].
            self._file_cache = None
            # Directory content cache. A mapping of directory -> { set of direct contents }.
            self._listing_cache = None


    ## Building file cache.

    def _build_cache(self):
        """ Rebuild internal file cache. This will make looking up files, errors notwithstanding, an O(1) lookup operation. """
        _log('Building cache...')

        with self._lock:
            self._file_cache = { self.ROOT: set() }
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
        _log.debug('Caching {prov} for {root}...', prov=provider, root=root)
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
        _log.debug('Caching {trans} for {pattern}...', trans=transformer, pattern=pattern.pattern)

        # Traverse paths to find matching files.
        for file in self._file_cache:
            if not pattern.search(file):
                continue

            # Gotcha.
            self._cache_transformed_file(transformer, file)

    def _cache_directory(self, provider, root, path):
        """ Add `path`, provided by `provider`, as a directory to the file cache. """
        _log.debug('Caching directory {path} <- {provider}...', path=path, provider=provider)

        with self._lock:
            self._listing_cache.setdefault(path, set())
        self._cache_entry(provider, root, path)

    def _cache_file(self, provider, root, path):
        """ Add `path`, provided by `provider`, as a file to the file cache. """
        _log.debug('Caching file {path} <- {provider}...', path=path, provider=provider)

        for pattern, transformers in self._transformers.items():
            if not pattern.search(path):
                continue

            consumed = False
            for transformer in transformers:
                consumed = self._cache_transformed_file(transformer, path)
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

    def _cache_transformed_file(self, transformer, path):
        """
        Add a transformed file at `path`, transformed by `transformer`, to the file cache.
        This will return whether or not the original file was consumed by `transformer`.
        It might fail to add the transformed file to the file cache if the transformers raises an error.

        If the transformer consumes the original file, this function will remove the original file from the file system,
        if it exists on it.
        """
        try:
            instance = transformer(path)
        except Exception as e:
            _log.warn('Error while transforming {path} with {tranformer}: {err}', path=path, transformer=transformer, err=e)
            return False

        if not instance.valid():
            return False
        _log.debug('Caching transformed file {path} <- {trans}...', path=path, trans=transformer)

        # Determine root directory of files.
        if instance.relative():
            parentdir = self.dirname(path)
        else:
            parentdir = self.ROOT

        # Mount as provider.
        self._cache_add_provider(instance, parentdir)

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

        if file not in self._file_cache:
            raise FileNotFound(file)

        for provider, mountpoint in reversed(self._file_cache[file]):
            localfile = file[len(mountpoint):]
            yield provider, localfile

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

            files = set()

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
         - open(fs, filename, **kwargs): open a file, has to raise one of the subclasses of `FileSystemError` on error, else return a subclass of `File`.
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

        if self._file_cache is None:
            self._build_cache()
        else:
            self._build_provider_cache(provider, path)

    def unmount(self, path, provider):
        """ Unmount `provider` from `path` in the virtual file system. Will trigger a full cache rebuild. """
        path = self.normalize(path)
        with self._lock:
            self._roots[path].remove(provider)

        self._build_cache()

    def transform(self, pattern, transformer):
        """
        TRANSFORMERS! TRANSFORMERS! MORE THAN MEETS THE EYE! TRANSFORMERS!
        Add `transformer` as a transformer for files matching `pattern`.

        `transformer` has to be a class(!) satisfying the provider API (see `mount`), plus the following API:
         - __init__(filename): initialize object, can raise any kind of error if the file is invalid.
         - valid(): return whether the file is valid according to the format this transformer parses.
         - consumes(): return whether the source file should be retained in the file system.
         - relative(): return whether files exposed by this transformer should be relative to the path of the source file or absolute.
        """
        pattern = re.compile(pattern, re.UNICODE)

        with self._lock:
            self._transformers.setdefault(pattern, [])
            self._transformers[pattern].append(transformer)

        if self._file_cache is None:
            self._build_cache()
        else:
            self._build_transformer_cache(transformer, pattern)

    def untransform(self, pattern, provider):
        """ Remove a transformer from the virtual file system. Will trigger a full cache rebuild. """
        pattern = re.compile(pattern, re.UNICODE)

        with self._lock:
            self._transformers[pattern].remove(provider)

        self._build_cache()

    def open(self, filename, **kwargs):
        """
        Open `filename` and return a corresponding `File` object. Will raise `FileNotFound` if the file was not found.
        Will only raise the error from the last attempted provider if multiple providers raise an error.
        """
        error = None

        filename = self.normalize(filename)
        for provider, localfile in self._providers_for_file(filename):
            try:
                return provider.open(localfile, **kwargs)
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
            return None
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


class File:
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
     - seek(position, relative=True) (if seekable, raises FileNotSeekable by default)
     - tell() (if seekable, raises FileNotSeekable by default)
    """

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

    def seek(self, position, relative=True):
        """ Seek in file. May raise `FileNotSeekable` if this file can't be seeked in. """
        raise FileNotSeekable(self)

    def tell(self):
        """ Tell current file position. May raise `FileNotSeekable` if this file can't be seeked in. """
        raise FileNotSeekable(self)

    def __enter__(self):
        """ Enter context management environment. """
        return self

    def __exit__(self, exctype, excvalue, exctraceback):
        """ Leave context management environment. """
        self.close()
