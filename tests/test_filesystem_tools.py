from rave import filesystem
from .support.filesystem import *


def test_normalize_current_dir(fs):
	assert fs.normalize('/abc/./def') == '/abc/def'

def test_normalize_parent_dir(fs):
	assert fs.normalize('/abc/../def') == '/def'

def test_normalize_seps(fs):
	assert fs.normalize('/abc//def') == '/abc/def'

def test_normalize_trailing_sep(fs):
	assert fs.normalize('/abc/def/') == '/abc/def'

def test_normalize_leading_sep(fs):
	assert fs.normalize('abc/def') == '/abc/def'

def test_normalize_trailing_parent(fs):
	assert fs.normalize('/abc/def/..') == '/abc'

def test_normalize_trailing_current(fs):
	assert fs.normalize('/abc/def/.') == '/abc/def'

def test_normalize_combo_1(fs):
	assert fs.normalize('abc/../def/./ghi') == '/def/ghi'

def test_normalize_combo_2(fs):
	assert fs.normalize('./def/./') == '/def'

def test_normalize_combo_3(fs):
	assert fs.normalize('//abc/../.././ghi/def//') == '/ghi/def'

def test_normalize_sane(fs):
	assert fs.normalize('/abc/def') == '/abc/def'


def test_basename(fs):
	assert fs.basename('/abc/def') == 'def'

def test_basename_root(fs):
	assert fs.basename('/') == ''

def test_basename_rootless(fs):
	assert fs.basename('abc/def') == 'def'

def test_basename_trailing_sep(fs):
	assert fs.basename('/abc/def/') == 'def'

def test_basename_normalization(fs):
	assert fs.basename('/abc/def/..') == 'abc'


def test_dirname(fs):
	assert fs.dirname('/abc/def') == '/abc'

def test_dirname_root(fs):
	assert fs.dirname('/') == '/'

def test_dirname_rootless(fs):
	assert fs.dirname('abc/def') == '/abc'

def test_dirname_trailing_sep(fs):
	assert fs.dirname('/abc/def/') == '/abc'

def test_dirname_normalization(fs):
	assert fs.dirname('/abc/def/..') == '/'