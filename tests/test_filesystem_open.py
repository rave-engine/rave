from rave import filesystem
from pytest import raises
from .support.filesystem import *


def test_open(dummyfs):
	with dummyfs.open('/x/a.txt') as f:
		assert isinstance(f, filesystem.File)

def test_open_invalid(fs):
	with raises(FileNotFoundError):
		fs.open('/nonexistent')

def test_open_directory(dummyfs):
	with raises(IsADirectoryError):
		dummyfs.open('/x')
