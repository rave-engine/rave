"""
rave game module.

This contains the code that ties everything together to run a single game.
"""
import threading
import rave.log
import rave.filesystem
import rave.execution
import rave.events

# The engine game!
engine = None

def current():
    """ Get currently running game. This is a convenience wrapper for rave.execution.current(). """
    env = rave.execution.current()
    if not env or not env.game:
        return None

    return env.game


## A game object.

class Game:
    """ A game session in rave. """
    def __init__(self, name, base=None):
        self.name = name
        self.base = base
        self.active_lock = threading.Lock()
        self.fs = rave.filesystem.FileSystem()
        self.events = rave.events.EventBus()
        self.env = rave.execution.ExecutionEnvironment(self)
        self.window = None
        self.mixer = None

        self.events.hook('game.suspend', self.suspend)
        self.events.hook('game.resume', self.resume)

        # Announce game creation over parent event bus.
        parent = current()
        if parent:
            parent.events.emit('game.created', self)

    def suspend(self, event):
        _log('Game suspending, acquiring main loop lock.')
        self.active_lock.acquire()

    def resume(self, event):
        _log('Game resuming, releasing main loop lock.')
        self.active_lock.release()

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__qualname__, self.name)


## Internals.

_log = rave.log.get(__name__)
