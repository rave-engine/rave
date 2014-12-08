from rave import filesystem
from pytest import raises
from .support.filesystem import *


def test_mount(fs):
	prov = DummyProvider({ '/', '/t', '/t/1.txt', '/t/2.txt' })
	fs.mount('/test', prov)
	assert fs.list() == { '/', '/test', '/test/t', '/test/t/1.txt', '/test/t/2.txt' }

def test_mount_merged_dirs(fs):
	prov = DummyProvider({ '/', '/t', '/t/1.txt', '/t/2.txt' })
	prov2 = DummyProvider({ '/', '/t2', '/t2/3.txt', '/t2/4.txt' })
	fs.mount('/test', prov)
	fs.mount('/test', prov2)
	assert fs.list() == { '/', '/test', '/test/t', '/test/t/1.txt', '/test/t/2.txt', '/test/t2', '/test/t2/3.txt', '/test/t2/4.txt' }

def test_mount_merged_files(fs):
	prov = DummyProvider({ '/', '/t', '/t/1.txt', '/t/2.txt' })
	prov2 = DummyProvider({ '/', '/t', '/t/3.txt', '/t/4.txt' })
	fs.mount('/test', prov)
	fs.mount('/test', prov2)
	assert fs.list() == { '/', '/test', '/test/t', '/test/t/1.txt', '/test/t/2.txt', '/test/t/3.txt', '/test/t/4.txt' }

def test_unmount(fs):
	prov = DummyProvider({ '/', '/t', '/t/1.txt', '/t/2.txt' })
	fs.mount('/test', prov)
	fs.unmount('/test', prov)
	assert fs.list() == { '/' }

def test_unmount_merged_dirs(fs):
	prov = DummyProvider({ '/', '/t', '/t/1.txt', '/t/2.txt' })
	prov2 = DummyProvider({ '/', '/t2', '/t2/3.txt', '/t2/4.txt' })
	fs.mount('/test', prov)
	fs.mount('/test', prov2)
	fs.unmount('/test', prov)
	assert fs.list() == { '/', '/test', '/test/t2', '/test/t2/3.txt', '/test/t2/4.txt' }

def test_unmount_merged_files(fs):
	prov = DummyProvider({ '/', '/t', '/t/1.txt', '/t/2.txt' })
	prov2 = DummyProvider({ '/', '/t', '/t/3.txt', '/t/4.txt' })
	fs.mount('/test', prov)
	fs.mount('/test', prov2)
	fs.unmount('/test', prov)
	assert fs.list() == { '/', '/test', '/test/t', '/test/t/3.txt', '/test/t/4.txt' }