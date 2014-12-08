import os
from rave import filesystem
from pytest import raises
from .support.filesystem import *


def test_file_read(dummyfs):
	with dummyfs.open('/x/a.txt') as f:
		assert f.read() == 'merry saltmas'

def test_file_read_amount(dummyfs):
	with dummyfs.open('/x/a.txt') as f:
		assert f.read(5) == 'merry'

def test_file_write(dummyfs):
	with dummyfs.open('/x/a.txt') as f:
		f.write('merry dankmas')
		f.seek(0, os.SEEK_SET)
		assert f.read() == 'merry dankmas'

def test_file_seek_set(dummyfs):
	with dummyfs.open('/x/a.txt') as f:
		f.seek(3, os.SEEK_SET)
		assert f.read() == 'ry saltmas'

def test_file_seek_end(dummyfs):
	with dummyfs.open('/x/a.txt') as f:
		f.seek(0, os.SEEK_END)
		assert f.read() == ''
