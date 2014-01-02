from nose.tools import eq_
from rave import filesystem as fs


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