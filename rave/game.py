"""
rave game module.

This contains the code that ties everything together to run a single game.
"""
import threading
import rave.log
import rave.events
import rave.filesystem
import rave.execution
import rave.backends
import rave.input
import rave.resources

_log = rave.log.get(__name__)


class Game:
    """ A game session in rave. """
    def __init__(self, name, base=None):
        self.name = name
        self.base = base
        self.active_lock = threading.Lock()

        self.fs = rave.filesystem.FileSystem()
        self.events = rave.events.EventBus()
        self.env = rave.execution.ExecutionEnvironment(self)
        self.dispatcher = rave.input.Dispatcher(self.events)
        self.resources = rave.resources.ResourceManager()
        self.window = None
        self.mixer = None

    def init(self):
        """ Initialize a game. """
        self.events.hook('game.suspend', self.suspend)
        self.events.hook('game.resume', self.resume)
        self.dispatcher.register_hooks()

        with self.env:
            self.events.emit('game.init', self)

    def run(self):
        """ Run the game. """
        running = True

        # Stop the event loop when a stop event was caught.
        def stop(event, b=None):
            nonlocal running
            running = False

        with self.events.hooked('game.stop', stop), self.env:
            self.events.emit('game.start', self)
            # Typical handle events -> update game state -> render loop.
            while running:
                with self.active_lock:
                    # Suspend main loop while lock is active: useful for when the OS requests an application suspend.
                    pass

                rave.backends.handle_events(self)
                if self.mixer:
                    self.mixer.render(None)
                if self.window:
                    self.window.render(None)

    def shutdown(self):
        """ Shut game down. """
        with self.env:
            self.fs.clear()

    def suspend(self, event):
        _log('Game suspending, acquiring main loop lock.')
        self.active_lock.acquire()

    def resume(self, event):
        _log('Game resuming, releasing main loop lock.')
        self.active_lock.release()

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__qualname__, self.name)


## Stateful API.

def current():
    """ Get currently running game. This is a convenience wrapper for rave.execution.current(). """
    env = rave.execution.current()
    if not env or not env.game:
        return None

    return env.game