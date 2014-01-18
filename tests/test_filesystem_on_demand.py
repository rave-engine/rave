from nose.tools import raises, eq_
from rave import filesystem as fs
from .filesystem_common import *


@dummyondemandsetup
def test_open_read(ondemand):
    with fs.open('on-demand://bar.txt') as f:
        eq_(f.read(), b'this is a test file.')

@dummyondemandsetup
def test_open_write(ondemand):
    with fs.open('on-demand://bar.txt') as f:
        f.write(b' test two.')
        eq_(f.read(), b'this is a test file. test two.')

@raises(fs.FileNotFound)
@dummyondemandsetup
def test_bogus_open(ondemand):
    with fs.open('on-demand://nope.jpg') as f:
        pass

@raises(fs.FileNotFound)
@dummyondemandsetup
def test_bogus_open2(ondemand):
    with fs.open('nope://bar.txt') as f:
        pass

@raises(fs.AccessDenied)
@dummyondemandsetup
def test_error_open(ondemand):
    DummyFile.ERROR = True
    try:
        file = fs.open('on-demand://bar.txt')
    finally:
        DummyFile.ERROR = False


@dummyondemandsetup
def test_remove(ondemand):
    fs.remove_on_demand(ondemand)
    eq_(fs.list(), set())

@raises(KeyError)
def test_bogus_remove():
    fs.remove_on_demand(None)
