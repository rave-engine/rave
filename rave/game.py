"""
rave game module.

This contains the code that ties everything together to run a single game.
"""
import rave.filesystem
import rave.execution
import rave.events

# The engine game!
engine = None


## A game object.

class Game:
    """ A game session in rave. """
    def __init__(self, name, base=None):
        self.name = name
        self.base = base
        self.fs = rave.filesystem.FileSystem()
        self.events = rave.events.EventBus()
        self.env = rave.execution.ExecutionEnvironment(self)

        rave.events.engine.emit('game.created', self)
