from nose.tools import raises, eq_
from rave import filesystem as fs
from .filesystem_common import *


def test_none():
	fs.clear()
	fs.transform('.txt$', DummyTransformer)
	eq_(fs.list(), [])

@dummytransformsetup
def test_transform(provider):
	eq_(set(fs.list()), { '/foo.txt', '/foo.rot13.txt' })

def test_subdir():
	fs.clear()
	fs.mount('/var', DummyProvider())
	fs.transform('.txt$', DummyTransformer)

	eq_(set(fs.list()), { '/var/foo.txt', '/var/foo.rot13.txt' })

@dummytransformsetup
def test_untransform(provider):
	fs.untransform('.txt$', DummyTransformer)
	eq_(fs.list(), [ '/foo.txt' ])

@raises(KeyError)
def test_bogus_untransform():
	fs.clear()
	fs.untransform('.bla', None)

@raises(KeyError)
@dummytransformsetup
def test_bogus_untransform2(provider):
	fs.untransform('.txt$', None)

@dummysetup
def test_consume(provider):
	DummyTransformer.CONSUMES = True
	fs.transform('.txt$', DummyTransformer)
	DummyTransformer.CONSUMES = False

	eq_(fs.list(), [ '/foo.rot13.txt' ])

def test_consume2():
	fs.clear()
	DummyTransformer.CONSUMES = True
	fs.transform('.txt$', DummyTransformer)
	fs.mount('/', DummyProvider())
	DummyTransformer.CONSUMES = False

	eq_(fs.list(), [ '/foo.rot13.txt' ])

def test_absolute():
	fs.clear()
	fs.mount('/var', DummyProvider())

	DummyTransformer.RELATIVE = False
	fs.transform('.txt$', DummyTransformer)
	DummyTransformer.RELATIVE = True

	eq_(set(fs.list()), { '/var/foo.txt', '/foo.rot13.txt' })

@dummytransformsetup
def test_open_read(provider):
	print(fs.list())
	with fs.open('/foo.rot13.txt') as f:
		eq_(f.read(), 'guvf vf n grfg svyr.')

@dummytransformsetup
def test_open_write(provider):
	with fs.open('/foo.rot13.txt') as f:
		f.write(' test two.')
		eq_(f.read(), 'guvf vf n grfg svyr. test two.')