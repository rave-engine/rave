from rave import events
from .support.events import *


def test_dispatch(bus):
	called = False
	def cb(ev):
		nonlocal called
		called = True

	bus.hook('rave.testing.test', cb)
	bus.emit('rave.testing.test')
	assert called

def test_dispatch_unregistered(bus):
	called = False
	def cb(ev):
		nonlocal called
		called = True

	bus.hook('rave.testing.test', cb)
	bus.emit('rave.testing.other')
	assert not called

def test_dispatch_multiple_calls(bus):
	call_count = 0
	def cb(ev):
		nonlocal call_count
		call_count += 1

	bus.hook('rave.testing.test', cb)

	for _ in range(5):
		bus.emit('rave.testing.test')

	assert call_count == 5

def test_dispatch_multiple_hooks(bus):
	cb_call_count = 0
	cb2_call_count = 0

	def cb(ev):
		nonlocal cb_call_count
		cb_call_count += 1

	def cb2(ev):
		nonlocal cb2_call_count
		cb2_call_count += 1

	bus.hook('rave.testing.test', cb)
	bus.hook('rave.testing.other', cb2)

	bus.emit('rave.testing.test')
	assert cb_call_count == 1
	assert cb2_call_count == 0

	bus.emit('rave.testing.other')
	assert cb_call_count == 1
	assert cb2_call_count == 1

	bus.emit('rave.testing.nonexistent')
	assert cb_call_count == 1
	assert cb2_call_count == 1


def test_dispatch_unhook(bus):
	call_count = 0
	def cb(ev):
		nonlocal call_count
		call_count += 1

	bus.hook('rave.testing.test', cb)
	bus.emit('rave.testing.test')
	assert call_count == 1

	bus.unhook('rave.testing.test', cb)
	bus.emit('rave.testing.test')
	assert call_count == 1

def test_dispatch_unhook_multiple_hooks(bus):
	cb_call_count = 0
	cb2_call_count = 0

	def cb(ev):
		nonlocal cb_call_count
		cb_call_count += 1

	def cb2(ev):
		nonlocal cb2_call_count
		cb2_call_count += 1

	bus.hook('rave.testing.test', cb)
	bus.hook('rave.testing.other', cb2)

	bus.emit('rave.testing.test')
	bus.emit('rave.testing.other')
	assert cb_call_count == 1
	assert cb2_call_count == 1

	bus.unhook('rave.testing.test', cb)
	bus.emit('rave.testing.test')
	assert cb_call_count == 1
	assert cb2_call_count == 1

	bus.emit('rave.testing.other')
	assert cb_call_count == 1
	assert cb2_call_count == 2

	bus.unhook('rave.testing.other', cb2)
	bus.emit('rave.testing.other')
	assert cb_call_count == 1
	assert cb2_call_count == 2