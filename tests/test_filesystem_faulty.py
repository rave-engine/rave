from rave import filesystem
from pytest import raises
from .support.filesystem import *


def test_faulty_open(fs):
	fs.mount('/x', FaultyProvider({ '/', '/y', '/y/a.txt', '/y/b.txt', }, { '/y/a.txt' }))
	with raises(filesystem.FileNotFound):
		fs.open('/x/y/a.txt')

def test_open_access_denied(fs):
	fs.mount('/x', FaultyProvider({ '/', '/y', '/y/a.txt', '/y/b.txt', }, { '/y/a.txt' }, err=filesystem.AccessDenied))
	with raises(filesystem.AccessDenied):
		fs.open('/x/y/a.txt')

def test_transfom_access_denied(fs):
	fs.mount('/x', FaultyProvider({ '/', '/y', '/y/a.txt', '/y/b.txt', }, { '/y/a.txt' }, err=filesystem.AccessDenied))
	fs.transform('.txt$', DummyTransformer)

	# The file couldn't be opened by the transformer, so /x/y/a.txt does not get transformed.
	assert fs.list() == { '/', '/x', '/x/y', '/x/y/a.txt', '/x/y/b.txt', '/x/y/b.txt.rot13' }

def test_transform_access_denied_after(fs):
	fs.transform('.txt$', DummyTransformer)
	fs.mount('/x', FaultyProvider({ '/', '/y', '/y/a.txt', '/y/b.txt', }, { '/y/a.txt' }, err=filesystem.AccessDenied))

	# Dito as test_transform_access_denied.
	assert fs.list() == { '/', '/x', '/x/y', '/x/y/a.txt', '/x/y/b.txt', '/x/y/b.txt.rot13' }

def test_transform_error(dummyfs):
	dummyfs.transform('.txt$', FaultyTransformer)

	# Assert nothing changed since the transformer error'd.
	assert dummyfs.list() == { '/', '/x', '/x/a.txt', '/x/b.png' }

def test_invalid_transformer(dummyfs):
	dummyfs.transform('.txt$', InvalidTransformer)

	# Assert nothing changed since the transformer was invalid.
	assert dummyfs.list() == { '/', '/x', '/x/a.txt', '/x/b.png' }