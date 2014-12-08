from rave import filesystem
from pytest import raises
from .support.filesystem import *


def test_empty(fs):
	assert fs.list() == { '/' }
	assert fs.listdir('/') == set()

def test_clear(dummyfs):
	dummyfs.clear()
	test_empty(dummyfs)



def test_list(dummyfs):
	assert dummyfs.list() == { '/', '/x', '/x/a.txt', '/x/b.png' }
	assert dummyfs.list('/x') == { '/', '/a.txt', '/b.png' }

def test_list_nested(nestedfs):
	assert nestedfs.list() == { '/', '/x', '/x/y', '/x/y/z', '/x/y/c.txt', '/x/y/p.png' }
	assert nestedfs.list('/x') == { '/', '/y', '/y/z', '/y/c.txt', '/y/p.png' }

def test_list_multiple(doublefs):
	assert doublefs.list() == { '/', '/x', '/x/a.txt', '/x/b.png', '/y', '/y/c.exe', '/y/d.jpg' }

def test_list_merged(mergedfs):
	assert mergedfs.list() == { '/', '/x', '/x/a.txt', '/x/b.png', '/x/c.exe', '/x/d.jpg' }

def test_list_nonexistent(dummyfs):
	with raises(filesystem.FileNotFound):
		dummyfs.list('/nonexistent')

def test_list_file(dummyfs):
	with raises(filesystem.NotADirectory):
		dummyfs.list('/x/a.txt')



def test_listdir(dummyfs):
	assert dummyfs.listdir('/') == { 'x' }
	assert dummyfs.listdir('/x') == { 'a.txt', 'b.png' }

def test_listdir_root(dummyfs):
	assert dummyfs.listdir() == dummyfs.listdir('/')

def test_listdir_merged(mergedfs):
	assert mergedfs.listdir('/x') == { 'a.txt', 'b.png', 'c.exe', 'd.jpg' }

def test_listdir_nonexistent(dummyfs):
	with raises(filesystem.FileNotFound):
		dummyfs.listdir('/nonexistent')

def test_listdir_file(dummyfs):
	with raises(filesystem.NotADirectory):
		dummyfs.listdir('/x/a.txt')



def test_parent_generation(parentlessfs):
	assert parentlessfs.list() == { '/', '/x', '/x/z', '/x/z/k.txt' }



def test_isfile(dummyfs):
	assert dummyfs.isfile('/x/a.txt')

def test_isfile_dir(dummyfs):
	assert not dummyfs.isfile('/')
	assert not dummyfs.isfile('/x')

def test_isfile_nonexistent(dummyfs):
	assert not dummyfs.isfile('/nonexistent')



def test_isdir(dummyfs):
	assert dummyfs.isdir('/x')
	assert dummyfs.isdir('/')

def test_isdir_file(dummyfs):
	assert not dummyfs.isdir('/x/a.txt')

def test_isdir_nonexistent(dummyfs):
	assert not dummyfs.isdir('/nonexistent')