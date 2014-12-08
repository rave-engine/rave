import os
import codecs
from io import StringIO
from pytest import fixture
from rave import filesystem


class DummyProvider:
	def __init__(self, files):
		self.files = files;

	def list(self):
		return self.files

	def has(self, filename):
		return filename in self.list()

	def open(self, filename, *args, **kwargs):                      
		if not self.has(filename):
			raise filesystem.FileNotFound(filename)
		if not self.isfile(filename):
			raise filesystem.NotAFile(filename)
		return DummyFile(self, filename)

	def isfile(self, filename):
		return self.has(filename) and '.' in filename

	def isdir(self, filename):
		return self.has(filename) and not self.isfile(filename)

class FaultyProvider(DummyProvider):
	def __init__(self, files, faulty_files, err=filesystem.FileNotFound):
		super().__init__(files)
		self.faulty_files = faulty_files
		self.error_class = err

	def open(self, filename, *args, **kwargs):
		if filename in self.faulty_files:
			raise self.error_class(filename)
		return super().open(filename, *args, **kwargs)


class DummyFile(filesystem.File):
	def __init__(self, parent, filename, content='merry saltmas'):
		self.parent = parent
		self.filename = filename
		self._buffer = StringIO(content)
		self._closed = False

	def close(self):
		if self._closed:
			raise filesystem.FileClosed(self.filename)
		self._closed = True

	def opened(self):
		return not self._closed

	def readable(self):
		return True

	def writable(self):
		return True

	def seekable(self):
		return True

	def read(self, amount=None):
		if self.closed:
			raise filesystem.FileClosed(self.filename)
		return self._buffer.read(amount)

	def write(self, buffer):
		if self.closed:
			raise filesystem.FileClosed(self.filename)
		return self._buffer.write(buffer)

	def seek(self, offset, mode=os.SEEK_CUR):
		return self._buffer.seek(offset, mode)

	def tell(self):
		return self._buffer.tell()


class DummyTransformer:
	CONSUME = False
	RELATIVE = False

	def __init__(self, filename, handle):
		self.filename = filename
		self.handle = handle
		self.files = [ self.filename + '.rot13' ]

	def list(self):
		return self.files

	def has(self, filename):
		return filename in self.list()

	def open(self, filename, *args, **kwargs):                        
		if not self.has(filename):
			raise filesystem.FileNotFound(filename)
		return ROT13File(self, filename, self.handle)

	def isfile(self, filename):
		return self.has(filename)

	def isdir(self, filename):
		return False

	def relative(self):
		return self.RELATIVE

	def consumes(self):
		return self.CONSUME

	def valid(self):
		return True

class FaultyTransformer:
	def __init__(self, filename, handle):
		raise FileNotFound(filename)

class InvalidTransformer(DummyTransformer):
	def valid(self):
		return False


class ROT13File(filesystem.File):
	def __init__(self, parent, filename, handle):
		self.parent = parent
		self.filename = filename
		self.handle = handle

	def close(self):
		return self.handle.close()

	def opened(self):
		return self.handle.opened()

	def readable(self):
		return self.handle.readable()

	def writable(self):
		return self.handle.writable()

	def seekable(self):
		return self.handle.seekable()

	def read(self, amount=None):
		return codecs.encode(self.handle.read(amount), 'rot13')

	def write(self, buffer):
		return self.handle.write(codecs.encode(buffer, 'rot13'))

	def seek(self, offset, mode=os.SEEK_CUR):
		return self.handle.seek(offset, mode)

	def tell(self):
		return self.handle.tell()



@fixture
def fs():
	return filesystem.FileSystem()

@fixture
def dummyfs():
	fs = filesystem.FileSystem()
	fs.mount('/x', DummyProvider({ '/a.txt', '/b.png' }))
	return fs

@fixture
def nestedfs():
	fs = filesystem.FileSystem()
	fs.mount('/x', DummyProvider({ '/y', '/y/c.txt', '/y/p.png', '/y/z' }))
	return fs

@fixture
def parentlessfs():
	fs = filesystem.FileSystem()
	fs.mount('/x', DummyProvider({ '/z/k.txt' }))
	return fs

@fixture
def doublefs():
	fs = filesystem.FileSystem()
	fs.mount('/x', DummyProvider({ '/a.txt', '/b.png' }))
	fs.mount('/y', DummyProvider({ '/c.exe', '/d.jpg' }))
	return fs

@fixture
def mergedfs():
	fs = filesystem.FileSystem()
	fs.mount('/x', DummyProvider({ '/a.txt', '/b.png' }))
	fs.mount('/x', DummyProvider({ '/c.exe', '/d.jpg' }))
	return fs

@fixture
def transfs():
	fs = dummyfs()
	fs.transform('\.txt$', DummyTransformer)
	return fs
