from rave import filesystem
from .support.filesystem import *


def test_filesystem_native_error():
	native_err = RuntimeError('test')
	err = filesystem.NativeError('Error', native_err)

	assert err.native_error == native_err