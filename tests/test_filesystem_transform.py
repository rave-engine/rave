from rave import filesystem
from pytest import raises
from .support.filesystem import *


def test_transform_list(transfs):
	assert transfs.list() == { '/', '/x', '/x/a.txt', '/x/a.txt.rot13', '/x/b.png' }

def test_transform_list_after(fs):
	fs.transform('.txt$', DummyTransformer)
	fs.mount('/x', DummyProvider({ '/a.txt', '/b.png' }))
	test_transform_list(fs)

def test_transform_list_relative(dummyfs):
	DummyTransformer.RELATIVE = True
	try:
		dummyfs.transform('.txt$', DummyTransformer)

		assert dummyfs.list() == { '/', '/x', '/x/a.txt', '/x/b.png', '/x/x', '/x/x/a.txt.rot13' }
	finally:
		DummyTransformer.RELATIVE = False

def test_transform_list_relative_after(fs):
	DummyTransformer.RELATIVE = True

	try:
		fs.transform('.txt$', DummyTransformer)
		fs.mount('/x', DummyProvider({ '/a.txt', '/b.png' }))

		assert fs.list() == { '/', '/x', '/x/a.txt', '/x/b.png', '/x/x', '/x/x/a.txt.rot13' }
	finally:
		DummyTransformer.RELATIVE = False


def test_transform_open(transfs):
	with transfs.open('/x/a.txt.rot13') as f:
		assert isinstance(f, filesystem.File)

def test_transform_open_invalid(transfs):
	with raises(filesystem.FileNotFound):
		transfs.open('/nonexistent.rot13')


def test_transform_read(transfs):
	with transfs.open('/x/a.txt.rot13') as f:
		assert f.read() == 'zreel fnygznf'


def test_untransform(transfs):
	transfs.untransform('\.txt$', DummyTransformer)
	assert transfs.list() == { '/', '/x', '/x/a.txt', '/x/b.png' }


def test_transform_consume():
	fs = dummyfs()

	DummyTransformer.CONSUME = True
	try:
		fs.transform('\.txt$', DummyTransformer)

		assert fs.list() == { '/', '/x', '/x/a.txt.rot13', '/x/b.png' }
	finally:
		DummyTransformer.CONSUME = False

def test_transform_consume_after(fs):
	DummyTransformer.CONSUME = True
	try:
		fs.transform('\.txt$', DummyTransformer)
		fs.mount('/x', DummyProvider({ '/a.txt', '/b.png' }))

		assert fs.list() == { '/', '/x', '/x/a.txt.rot13', '/x/b.png' }
	finally:
		DummyTransformer.CONSUME = False
