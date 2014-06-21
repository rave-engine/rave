"""
rave game module.

This contains the code that ties everything together to run a single game.
"""
import threading
from . import log


## Internal.

_log = log.get(__name__)
_lock = threading.Lock()
_current_games = {}

def _identifier():
    """ Get unique identifier for all possible parallel mechanisms. """
    return threading.current_thread().ident


## API.

def current():
    """ Get current game object for whatever parallel mechanism is used, or None if no game is active. """
    with _lock:
        id = _identifier()
        return _current_games.get(id)

def set_current(game):
    """ Set current game for whatever parallel mechanism is used, or None if the game has stopped. """
    with _lock:
        id = _identifier()

        if game is None:
            del _current_games[id]
        else:
            _current_games[id] = game
