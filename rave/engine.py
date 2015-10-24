import rave.log
import rave.execution
import rave.filesystem
import rave.events
import rave.loader
import rave.modularity
import rave.backends

_log = rave.log.get(__name__)


engine = None

class Engine:
    """ The engine. """
    def __init__(self):
        self.fs = rave.filesystem.FileSystem()
        self.events = rave.events.EventBus()
        self.games = []

    def init(self):
        rave.modularity.load_all()
        rave.backends.select_all()

    def shutdown(self):
        rave.loader.remove_hooks()

    def run_game(self, game):
        self.games.append(game)
        self.events.emit('engine.new_game', game)
        game.init()
        game.run()
        game.shutdown()

    def current_game(self):
        """ Get currently running game. This is a convenience wrapper for rave.execution.current(). """
        env = rave.execution.current()
        if not env or not env.game:
            return None

        return env.game