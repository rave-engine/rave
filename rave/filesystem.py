# rave's virtual file system.
import builtins
import re
import threading

# File system roots. A mapping of path -> [ list of providers ].
_roots = {}
# A reverse mapping for _roots: provider -> mount path.
_mount_points = {}
# On-demand providers. A list of providers.
_on_demands = []
# Transforming providers. A mapping of extension -> [ list of providers ].
_transformers = {}
# File/directory list cache. A mapping of filename -> [ list of providers ].
_files = None
# Directory content cache. A mapping of directory -> { set of direct contents }.
_contents = None
# Lock when rebuilding cache.
_cache_lock = threading.Lock()
# Lock when modifying providers.
_register_lock = threading.Lock()
# Canonical path separator.
PATH_SEPARATOR = '/'

# Errors.
class FileSystemError(Exception): pass
class FileNotFound(FileSystemError): pass
class AccessDenied(FileSystemError): pass
class FileNotReadable(FileSystemError): pass
class FileNotWritable(FileSystemError): pass
class FileNotSeekable(FileSystemError): pass
class FileClosed(FileSystemError): pass
class NotAFile(FileSystemError): pass
class NotADirectory(FileSystemError): pass

## Internals.

def _cache_build():
	""" Build file list from existing roots and transformers. """
	global _roots, _files, _contents

	_files = {}
	_contents = {}
	for root, providers in _roots.items():
		for provider in providers:
			_cache_add_provider(provider, root)

def _cache_add_provider(provider, root):
	""" Build cache entry for a root. """
	# Add root and all its parents.
	current = root
	while True:
		parent = dirname(current)
		if parent == current:
			break

		_cache_add_directory(provider, parent)
		current = parent

	for filename in provider.list():
		path = normalize(join(root, filename))

		if provider.isdir(path):
			_cache_add_directory(provider, path)
		else:
			_cache_add_file(provider, path)

def _cache_add_directory(provider, directory):
	""" Build cache entry for directory. """
	global _files, _contents, _cache_lock

	parent = normalize(dirname(directory))
	with _cache_lock:
		if directory not in _files:
			_files[directory] = []
		if provider not in _files[directory]:
			_files[directory].append(provider)

		# Add directory to parent directory content cache.
		if parent != directory:
			if parent not in _contents:
				_contents[parent] = set()
			_contents[parent].add(directory[len(parent):].strip(PATH_SEPARATOR))

def _cache_add_file(provider, filename):
	""" Build cache entry for file. Will take file through any applicable transformers. """
	global _files, _contents, _transformers, _cache_lock

	# Check if we have a transformer for this file.
	for pattern, transformers in _transformers.items():
		if not pattern.search(filename):
			continue

		# Transform until we are out of transformers or consumed our input file.
		consumed = False
		for transformer in transformers:
			consumed = _cache_add_transformer_for_file(transformer, filename)
			if consumed:
				break
		# Break from the nested loop.
		if consumed:
			break
	else:
		parent = normalize(dirname(filename))

		# No file consumption occurred, add file to cache.
		with _cache_lock:
			if filename not in _files:
				_files[filename] = []
			if provider not in _files[filename]:
				_files[filename].append(provider)

			# Add file to parent directory content cache.
			if parent not in _contents:
				_contents[parent] = set()
			_contents[parent].add(filename[len(parent):].strip(PATH_SEPARATOR))

def _cache_add_transformer(pattern, provider):
	""" Add transformer to cache: process any files affected by transformer. """
	# Find matching files for transformer. Make a copy because we might modify the list.
	for filename in builtins.list(_files.keys()):
		if not pattern.search(filename):
			continue

		consumed = _cache_add_transformer_for_file(provider, filename)
		# Remove consumed file.
		if consumed:
			with _cache_lock:
				del _files[filename]
				break

def _cache_add_transformer_for_file(provider, filename):
	""" Attempt to add `provider` as transformer for `filename`. Returns a tuple of (succeeded, consumed). """
	global _mount_points

	# Try to load file in transformer.
	try:
		transformer = provider(filename)
	except:
		return False
	if not transformer.valid():
		return False

	# It all worked, process the transformer.
	if provider.relative():
		mountpoint = dirname(filename)
	else:
		mountpoint = PATH_SEPARATOR

	_cache_add_provider(transformer, mountpoint)
	with _register_lock:
		_mount_points[transformer] = mountpoint

	return provider.consumes()

def _providers_for_file(filename):
	""" Generate a list of providers that may be able to provide `filename`. """
	global _files, _on_demands, _mount_points

	# Fill the file cache if it doesn't exist yet.
	if not _files:
		_cache_build()

	# Check if any local provider can provide it.
	normalized = normalize(filename)
	if normalized in _files:
		for provider in _files[normalized]:
			# Strip mount point for provider. Transformers don't have a mount point entry but are mounted at the root.
			prefix = _mount_points[provider]
			localname = PATH_SEPARATOR + normalized[len(prefix):].lstrip(PATH_SEPARATOR)
			yield provider, localname

	# Now check on-demand providers.
	for provider in _on_demands:
		if provider.has(filename):
			yield provider, filename

## API.

# Delete fucking everything.

def clear():
	""" Clear the entire file system. Removes all roots, on-demand providers and transformers. """
	global _roots, _contents, _on_demands, _transformers, _mount_points, _files, _cache_lock, _register_lock

	with _cache_lock, _register_lock:
		_roots = {}
		_contents = {}
		_on_demands = []
		_transformers = {}
		_mount_points = {}
		_files = None

# Mounting/unmounting.

def mount(path, provider):
	"""
	Mount `provider` at `path` in the virtual file system.

	`provider` must be an object satisfying the following API:
	 - list(): return a list of all file names (including folders) this provider can provide.
	 - has(filename): return whether this provider can open given file.
	 - open(filename): open a file, has to raise one of the subclasses of `FileSystemError` on error, else return a subclass of `File`.
	 - isfile(filename): check if the given file is a file, should raise applicable `FileSystemError` subclass if applicable,
	     except for NotAFile/NotADirectory, or return a boolean.
	 - isdir(filename): check if the given file is a directory, should raise applicable `FileSystemError` subclass if applicable,
	     except for NotAFile/NotADirectory, or return a boolean.

	A path can be provided by different providers. Their file lists will be merged.
	Conflicting files will be handled as such:
	 - If the base path for the providers are the same, the first provider that has been mounted will serve it.
	 - If the base paths differ, the provider with the most specific base path will serve it.
	 - If an error occurs while serving the file, the next provider according to these rules will serve it.
	"""
	global _roots, _mount_points, _files, _register_lock
	path = normalize(path)

	with _register_lock:
		if path not in _roots:
			_roots[path] = []
		_roots[path].append(provider)
		_mount_points[provider] = path

	# Add to file cache.
	if _files:
		_cache_add_provider(provider, path)
	else:
		_cache_build()

def unmount(path, provider):
	""" Remove `provider` from `path in the virtual file system. Will raise `KeyError` if the provider could not be found. """
	global _roots, _mount_points, _register_lock
	path = normalize(path)

	with _register_lock:
		try:
			_roots[path].remove(provider)
			del _mount_points[provider]
		except ValueError:
			raise KeyError(provider)

	# Rebuild cache.
	_cache_build()

# Transforming.

def transform(pattern, provider):
	"""
	TRANSFORMERS! TRANSFORMERS! MORE THAN MEETS THE EYE! TRANSFORMERS!
	Add `provider` as a transformer for files matching `pattern`.

	`provider` has to be a class satisfying the following API:
	 - (static) consumes(): return whether the source file should be retained in the file system.
	 - (static) relative(): return whether files exposed by this transformer should be relative to the source path or absolute.
	 - __init__(filename): initialize object, can raise any kind of error if the file is invalid.
	 - valid(): return whether the file is valid according to the format this transformer parses.
	 - list(): return a list of files (including folders, if any) created by this transformer.
	 - has(filename): return whether this provider can open given file.
	 - open(filename): open a file, has to raise one of the subclasses of `FileSystemError` on error, else return a subclass of `File`.
	 - isfile(filename): check if the given file is a file, should raise applicable `FileSystemError` subclass if applicable,
	     except for NotAFile/NotADirectory, or return a boolean.
	 - isdir(filename): check if the given file is a directory, should raise applicable `FileSystemError` subclass if applicable,
	     except for NotAFile/NotADirectory, or return a boolean.
	"""
	global _transformers, _files, _register_lock

	pattern = re.compile(pattern, re.UNICODE)
	with _register_lock:
		if pattern not in _transformers:
			_transformers[pattern] = []
		_transformers[pattern].append(provider)

	# Process file cache changes.
	if _files:
		_cache_add_transformer(pattern, provider)
	else:
		_cache_build()

def untransform(pattern, provider):
	"""
	The enemy's return is certain.
	Remove `provider` as a transformer for filenames matching `pattern`.
	Will raise `KeyError` if the transformer could not be found.
	"""
	global _transformers, _register_lock

	pattern = re.compile(pattern, re.UNICODE)
	with _register_lock:
		try:
			_transformers[pattern].remove(provider)
		except ValueError:
			raise KeyError(provider)

	# Rebuild file cache.
	_cache_build()

# On-demand providers.

def add_on_demand(provider):
	"""
	Add `provider` as 'on-demand' provider for filenames matching `pattern`.

	`provider` is expected to be an object satisfying the following API:
	 - has(filename): return whether this provider can open given file.
	 - open(filename): open a file, has to raise one of the subclasses of `FileSystemError` on error, else return a subclass of `File`.
	 """
	global _on_demands, _register_lock

	with _register_lock:
		_on_demands.append(provider)

def remove_on_demand(provider):
	"""
	Remove `provider` as on-demand provider for filenames matching `pattern`.
	Will raise a `KeyError` if the provider could not be found.
	"""
	global _on_demands, _register_lock

	with _register_lock:
		try:
			_on_demands.remove(provider)
		except ValueError:
			raise KeyError(provider)

# Listing and opening.

def list(subdir=None):
	""" Return a list all files in the virtual file system. """
	global _files

	# Rebuild list if we need to.
	if not _files:
		_cache_build()

	return set(_files.keys())

def open(filename, *args, **kwargs):
	"""
	Open `filename` and return a corresponding `File` object. Will raise `FileNotFound` if the file was not found.
	Will only raise the error from the latest attempted provider if all providers raise.
	"""
	error = FileNotFound(filename)

	# Check if any local provider can provide it.
	for provider, filename in _providers_for_file(filename):
		try:
			return provider.open(filename, *args, **kwargs)
		except FileNotFound:
			continue
		except Exception as e:
			error = e

	# No provider available for this poor file. Let the user know. :-(
	raise error

# Utility functions.

def dirname(path):
	""" Return the directory part of the given path. """
	path = path.rstrip(PATH_SEPARATOR).rsplit(PATH_SEPARATOR, 1)[0]
	return normalize(path)

def basename(path):
	""" Return the filename part of the given path. """
	return path.rstrip(PATH_SEPARATOR).rsplit(PATH_SEPARATOR, 1)[1]

def join(*paths):
	""" Join path pieces by path separator. """
	return PATH_SEPARATOR.join(paths)

def exists(filename):
	""" Check if `filename` exists in the file system. """
	global _files

	if not _files:
		_cache_build()

	# Quick and easy test.
	normalized = normalize(filename)
	if normalized in _files:
		return True

	# Else, check all providers.
	return any(provider.has(filename) for provider, filename in _providers_for_file(filename))

def listdir(directory):
	""" Return the contents of a directory as a set. """
	global _files, _contents

	directory = normalize(directory)
	if directory not in _contents:
		if directory in _files:
			raise NotADirectory(directory)
		raise FileNotFound(directory)

	return _contents[directory]

def isfile(filename):
	""" Check if `filename` represents a file. """
	for provider, filename in _providers_for_file(filename):
		try:
			return provider.isfile(filename)
		except FileNotFound:
			continue

	return False

def isdir(filename):
	""" Check if `filename` represents a directory. """
	global _roots

	for provider, filename in _providers_for_file(filename):
		try:
			return provider.isdir(filename)
		except FileNotFound:
			continue

	return False

def split(path):
	""" Split path by path separator. """
	return path.split(PATH_SEPARATOR)

def normalize(path):
	""" Normalize path to canonical path. """
	# Get pieces.
	pieces = split(path)

	# Remove empty or redundant directories.
	pieces = [ piece for piece in pieces if piece and piece != '.' ]
	# Remove parent directory entries.
	while '..' in pieces:
		i = pieces.index('..')
		del pieces[i]
		# The preceding piece, too.
		if i > 0:
			del pieces[i - 1]

	return PATH_SEPARATOR + join(*pieces)


## Base classes.

class File:
	"""
	An open file in the virtual file system.
	Subclasses are expected to at least override the following:
	 - opened()
	 - readable() (if readable, returns False by default)
	 - writable() (if writable, returns False by default)
	 - seekable() (if seekable, returns False by default)
	 - close()
	 - read(amount=None) (if readable)
	 - write(data) (if writable)
	 - seek(position, relative=True) (if seekable)
	 - tell() (if seekable)
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
