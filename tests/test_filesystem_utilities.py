from nose.tools import eq_, ok_, raises
from rave import filesystem as fs
from .filesystem_common import *

def test_list_none():
	fs.clear()
	eq_(fs.list(), set())

@dummysetup
def test_list(provider):
	eq_(fs.list(), { '/', '/foo.txt'})

def test_list_subdir():
	fs.clear()
	fs.mount('/var', DummyProvider())
	eq_(fs.list(), { '/', '/var', '/var/foo.txt' })
	eq_(fs.list('/var'), { '/', '/foo.txt' })

@raises(fs.FileNotFound)
def test_list_bogus():
	fs.clear()
	fs.list('/baz')

@raises(fs.NotADirectory)
@dummysetup
def test_list_bogus(provider):
	fs.list('/foo.txt')


def test_dirname():
	eq_(fs.dirname('/var/foo/bar.txt'), '/var/foo')

def test_basename():
	eq_(fs.basename('/var/foo/bar.txt'), 'bar.txt')

def test_normalize_pathsep():
	eq_(fs.normalize('//var//foo///bar/z.txt'), '/var/foo/bar/z.txt')

def test_normalize_parentdir():
	eq_(fs.normalize('//var/../'), '/')

def test_normalize_leftover_parentdir():
	eq_(fs.normalize('/../var/foo/../bar//'), '/var/bar')


@dummysetup
def test_exists(provider):
	ok_(fs.exists('/foo.txt'))

@dummytransformsetup
def test_exists_transformer(provider):
	ok_(fs.exists('/foo.txt'))

@dummyondemandsetup
def test_exists_ondemand(ondemand):
	ok_(fs.exists('on-demand://z.txt'))

@dummysetup
def test_exists_bogus(provider):
	ok_(not fs.exists('/baz'))
	ok_(not fs.exists('/baz.txt'))


@dummysetup
def test_isfile(provider):
	ok_(fs.isfile('/foo.txt'))

def test_isfile_subdir():
	fs.clear()
	fs.mount('/var', DummyProvider())

	ok_(fs.isfile('/var/foo.txt'))

def test_isfile_none():
	fs.clear()
	ok_(not fs.isfile('/bar.txt'))

@dummysetup
def test_isfile_bogus(provider):
	ok_(not fs.isfile('/baz/foo.txt'))

@dummytransformsetup
def test_isfile_transformer(provider):
	ok_(fs.isfile('/foo.rot13.txt'))

@dummyondemandsetup
def test_isfile_ondemand(ondemand):
	ok_(fs.isfile('on-demand://z.txt'))

def test_isfile_ondemand_bogus():
	fs.clear()
	fs.add_on_demand(BuggyListOnDemand())

	ok_(not fs.isfile('buggy-demand://'))


@dummysetup
def test_isdir(provider):
	ok_(fs.isdir('/'))

def test_isdir_none():
	fs.clear()
	ok_(not fs.isdir('/'))

@dummysetup
def test_isdir_bogus(provider):
	ok_(not fs.isdir('/baz'))

def test_isdir_subdir():
	fs.clear()
	fs.mount('/var', DummyProvider())

	ok_(fs.isdir('/var'))

def test_isdir_ondemand_bogus():
	fs.clear()
	fs.add_on_demand(BuggyListOnDemand())

	ok_(not fs.isdir('buggy-demand://'))


@dummysetup
def test_listdir(provider):
	eq_(fs.listdir('/'), { 'foo.txt' })

def test_listdir_subdir():
	fs.clear()
	fs.mount('/var', DummyProvider())

	eq_(fs.listdir('/var'), { 'foo.txt' })

@raises(fs.FileNotFound)
@dummysetup
def test_listdir_bogus(provider):
	fs.listdir('/var')

@raises(fs.NotADirectory)
@dummysetup
def test_listdir_bogus2(provider):
	fs.listdir('/foo.txt')

def test_listdir_ondemand():
	fs.clear()
	fs.add_on_demand(DummyListOnDemand())

	eq_(fs.listdir('on-demand://'), { 'on-demand:///z.txt' })

@raises(fs.FileNotFound)
@dummyondemandsetup
def test_listdir_ondemand_bogus(ondemand):
	fs.listdir('on-demand://')

@raises(fs.AccessDenied)
def test_listdir_ondemand_buggy():
	fs.clear()
	fs.add_on_demand(BuggyListOnDemand())

	fs.listdir('on-demand://')


@buggysetup
def test_buggy_exists(provider):
	ok_(fs.exists('/bar.txt'))

@buggysetup
def test_buggy_isfile(provider):
	ok_(fs.isfile('/bar.txt'))

@buggysetup
def test_buggy_isdir(provider):
	ok_(fs.isdir('/'))