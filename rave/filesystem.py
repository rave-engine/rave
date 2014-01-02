# rave's virtual file system.
import builtins
import re

# File system roots. A mapping of path -> [ list of providers ].
_roots = {}
# On-demand providers. A mapping of regexp -> [ list of providers ].
_on_demands = {}
# Transforming providers. A mapping of extension -> [ list of providers ].
_transformers = {}
# File list cache.
_files = None
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


## Internals.

def _cache_build():
	""" Build file list from existing roots and transformers. """
	global _roots, _files
	_files = {}

	for root, providers in _roots.items():
		for provider in providers:
			_cache_add_provider(provider, root)

def _cache_add_provider(provider, root):
	""" Build cache entry for a root. """
	for filename in provider.list():
		path = normalize(join(root, filename))
		_cache_add_file(provider, path)

def _cache_add_file(provider, filename):
	"""
	Build cache entry for file. Will take file through any applicable transformers.
	"""
	global _files, _transformers

	# Check if we have a transformer for this file.
	for pattern, transformers in _transformers.items():
		if not pattern.search(filename):
			continue

		# Transform until we are out of transformers or consumed our input file.
		consumed = False
		for transformer in transformers:
			consumed = _cache_add_transformer(transformer, filename)
			if consumed:
				break
		# Break from the nested loop.
		if consumed:
			break
	else:
		# No file consumption occurred, add file to cache.
		if filename not in _files:
			_files[filename] = []
		_files[filename].append(provider)

def _cache_add_transformer(provider, filename):
	""" Attempt to add `provider` as transformer for `filename`. Returns a tuple of (succeeded, consumed). """
	# Try to load file in transformer.
	try:
		transformer = provider(filename)
	except:
		return False
	if not transformer.valid():
		return False

	# It all worked, process the transformer.
	if provider.relative():
		_cache_add_provider(transformer, dirname(filename))
	else:
		_cache_add_provider(transformer, '/')

	return provider.consumes()


## API.

# Delete fucking everything.

def clear():
	""" Clear the entire file system. Removes all roots, on-demand providers and transformers. """
	global _roots, _on_demands, _transformers, _files

	_roots = {}
	_on_demands = {}
	_transformers = {}
	_files = None

# Mounting/unmounting.

def mount(path, provider):
	"""
	Mount `provider` at `path` in the virtual file system.

	`provider` must be an object satisfying the following API:
	 - list(): return a list of all file names this provider can provide.
	 - has(filename): return whether this provider can open given file.
	 - open(filename): open a file, has to raise one of the subclasses of `FileSystemError` on error, else return a subclass of `File`.

	A path can be provided by different providers. Their file lists will be merged.
	Conflicting files will be handled as such:
	 - If the base path for the providers are the same, the first provider that has been mounted will serve it.
	 - If the base paths differ, the provider with the most specific base path will serve it.
	 - If an error occurs while serving the file, the next provider according to these rules will serve it.
	"""
	global _roots, _files
	if path not in _roots:
		_roots[path] = []

	_roots[path].append(provider)

	# Add to file cache.
	if _files:
		_cache_add_provider(provider, path)
	else:
		_cache_build()

def unmount(path, provider):
	""" Remove `provider` from `path in the virtual file system. Will raise `KeyError` if the provider could not be found. """
	global _roots

	try:
		_roots[path].remove(provider)
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
	 - list(): return a list of files created by this transformer.
	 - has(filename): return whether this provider can open given file.
	 - open(filename): open a file, has to raise one of the subclasses of `FileSystemError` on error, else return a subclass of `File`.
	"""
	global _transformers, _files

	pattern = re.compile(pattern, re.UNICODE)
	if pattern not in _transformers:
		_transformers[pattern] = []
	_transformers[pattern].append(provider)

	# Process file cache changes.
	if _files:
		# Find matching files for transformer. Make a copy because we might modify the list.
		for filename in builtins.list(_files.keys()):
			if not pattern.search(filename):
				continue

			consumed = _cache_add_transformer(provider, filename)
			# Remove consumed file.
			if consumed:
				del _files[filename]
				break
	else:
		_cache_build()

def untransform(pattern, provider):
	"""
	The enemy's return is certain.
	Remove `provider` as a transformer for filenames matching `pattern`.
	Will raise `KeyError` if the transformer could not be found.
	"""
	global _transformers

	pattern = re.compile(pattern, re.UNICODE)
	try:
		_transformers[pattern].remove(provider)
	except ValueError:
		raise KeyError(provider)

	# Rebuild file cache.
	_cache_build()

# On-demand providers.

def add_on_demand(pattern, provider):
	"""
	Add `provider` as 'on-demand' provider for filenames matching `pattern`.

	`provider` is expected to be an object satisfying the following API:
	 - has(filename): return whether this provider can open given file.
	 - open(filename): open a file, has to raise one of the subclasses of `FileSystemError` on error, else return a subclass of `File`.
	 """
	global _on_demands

	pattern = re.compile(pattern, re.UNICODE)
	if pattern not in _on_demands:
		_on_demands[pattern] = []
	_on_demands[pattern].append(provider)

def remove_on_demand(pattern, provider):
	"""
	Remove `provider` as on-demand provider for filenames matching `pattern`.
	Will raise a `KeyError` if the provider could not be found.
	"""
	global _on_demands

	pattern = re.compile(pattern, re.UNICODE)
	try:
		_on_demands[pattern].remove(provider)
	except ValueError:
		raise KeyError(provider)

# Listing and opening.

def list():
	""" Return a list all files in the virtual file system. """
	global _files

	# Rebuild list if we need to.
	if not _files:
		_cache_build()

	return builtins.list(_files.keys())

def open(filename):
	"""
	Open `filename` and return a corresponding `File` object. Will raise `FileNotFound` if the file was not found.
	Will only raise the error from the latest attempted provider if all providers raise.
	"""
	global _files, _on_demands

	# We can't do much without a file cache.
	if not _files:
		_cache_build()
	error = FileNotFound(filename)

	# Check if any local provider can provide it.
	if filename in _files:
		# Let's rock. Iterate through all providers that have the file until we get one that will open it.
		for provider in _files[filename]:
			try:
				return provider.open(filename)
			except FileNotFound:
				pass
			except Exception as e:
				# Store error.
				error = e

	# See if any on-demand provider can provide it.
	for pattern, providers in _on_demands.items():
		if not pattern.search(filename):
			continue

		# Iterate through providers for pattern.
		for provider in providers:
			if not provider.has(filename):
				continue

			try:
				return provider.open(filename)
			except FileNotFound:
				pass
			except Exception as e:
				# Store error.
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

	return '/' + join(*pieces)


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
