""" A modular and extensible visual novel engine. """

__version__ = '0.1.0'
__version_info__ = (0, 1, 0)
__author__ = 'rave developers and contributors'
__license__ = 'BSD'

from . import common
from . import log
from . import events
from . import execution
from . import filesystem
from . import loader
from . import modularity
from . import backends
from . import rendering
from . import resources
from . import bootstrap
from . import game
from . import main
