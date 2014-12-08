from rave import events
from pytest import fixture


@fixture
def bus():
	return events.EventBus()
