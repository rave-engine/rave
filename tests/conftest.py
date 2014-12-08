from pytest import fixture
import rave


@fixture(scope='session', autouse=True)
def silence_logger(request):
	# Silence all log output.
	rave.log.set_level(0)