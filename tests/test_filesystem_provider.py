from nose.tools import raises, eq_
from rave import filesystem as fs
from .filesystem_common import *


def test_none():
    fs.clear()
    eq_(fs.list(), [])

@dummysetup
def test_mount(provider):
    eq_(fs.list(), [ '/foo.txt' ])

@dummysetup
def test_unmount(provider):
    fs.unmount('/', provider)
    eq_(fs.list(), [])

@dummysetup
def test_mount_successive(provider):
    provider2 = DummyProvider()

    eq_(fs.list(), [ '/foo.txt' ])
    fs.mount('/var', provider2)
    eq_(set(fs.list()), { '/foo.txt', '/var/foo.txt' })

@dummysetup
def test_unmount_successive(provider):
    provider2 = DummyProvider()
    fs.mount('/var', provider2)

    fs.unmount('/', provider)
    eq_(fs.list(), [ '/var/foo.txt' ])
    fs.unmount('/var', provider2)
    eq_(fs.list(), [])

@raises(KeyError)
def test_bogus_unmount():
    fs.clear()
    fs.unmount('/', None)

@raises(KeyError)
@dummysetup
def test_bogus_unmount2(provider):
    fs.unmount('/', None)

@raises(fs.FileNotFound)
def test_bogus_open():
    with fs.open('/foo.txt') as f:
        pass

@raises(fs.AccessDenied)
@dummysetup
def test_error_open(provider):
    DummyFile.ERROR = True
    try:
        file = fs.open('/foo.txt')
    finally:
        DummyFile.ERROR = False

@dummysetup
def test_open_read(provider):
    with fs.open('/foo.txt') as f:
        eq_(f.read(), b'this is a test file.')

@dummysetup
def test_open_write(provider):
    with fs.open('/foo.txt') as f:
        f.write(b' test two.')
        eq_(f.read(), b'this is a test file. test two.')
