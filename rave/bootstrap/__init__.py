"""
rave bootstrap system.

The bootstrap system allows rave to be, as the name implies, bootstrapped using various means.
Bootstrapping is done in two stages: the global engine bootstrap, and the game-specific bootstrap.
The engine is bootstrapped using rave.bootstrap.bootstrap_engine(), the game using rave.bootstrap.bootstrap_game().
Both functions take an optional bootstrapper name, if none is given an attempt will be made to auto-detect the bootstrapper.
rave.bootstrap.bootstrap_game() also takes the 'base' parameter, which indicates some kind of identifier for the bootstrapper
to find the game with.

Bootstrappers should be placed in rave/bootstrappers/ and should implement the following API:
- bootstrap_modules(): bootstrap essential engine modules.
- bootstrap_filesystem(): bootstrap engine file system and mount rave.bootstrap.ENGINE_MOUNT,
    rave.bootstrap.MODULE_MOUNT and rave.bootstrap.COMMON_MOUNT on the file system.
- bootstrap_game_filesystem(): bootstrap game file system and mount rave.bootstrap.GAME_MOUNT.
"""
import importlib

from rave import __version__
import rave.loader
import rave.modularity
import rave.log
import rave.game


ENGINE_MOUNT = '/.rave'
ENGINE_PACKAGE = 'rave'
MODULE_MOUNT = '/.modules'
MODULE_PACKAGE = 'rave.modules'
GAME_MOUNT = '/'
GAME_PACKAGE = 'rave.game'
COMMON_MOUNT = '/.common'


## Internal.

_log = rave.log.get(__name__)

def _find_engine_bootstrapper():
    """ Determine the bootstrapper to use for bootstrapping the engine parts. """
    # We currently only have one bootstrapper.
    return 'filesystem'

def _find_game_bootstrapper(base):
    """ Determine the bootstrapper to use for bootstrapping the game. """
    # We still only have one bootstrapper.
    return 'filesystem'


## API.

def bootstrap_engine(bootstrapper=None):
    """ Bootstrap the engine. """
    _log('This is rave v{ver}.', ver=__version__)

    rave.game.engine = rave.game.Game('<engine>')

    with rave.game.engine.env:
        _log('Installing hooks...')
        rave.loader.install_hook(ENGINE_PACKAGE, [ ENGINE_MOUNT ])
        rave.loader.install_hook(MODULE_PACKAGE, [ MODULE_MOUNT ], cls=rave.modularity.ModuleLoader)
        rave.loader.install_hook(GAME_PACKAGE, [ GAME_MOUNT ])

        if not bootstrapper:
            bootstrapper = _find_engine_bootstrapper()

        _log('Engine bootstrapper: {name}', name=bootstrapper)
        bootstrapper = importlib.import_module('rave.bootstrap.' + bootstrapper)

        # We bootstrap vital modules first that are likely needed to bootstrap the file system.
        _log.debug('Bootstrapping engine modules...')
        bootstrapper.bootstrap_modules()

    return rave.game.engine


def bootstrap_game(bootstrapper=None, base=None):
    """ Bootstrap the game with `base` as game base. """
    if not bootstrapper:
        bootstrapper = _find_game_bootstrapper(base)

    _log('Game bootstrapper: {name}', name=bootstrapper)
    bootstrapper = importlib.import_module('rave.bootstrap.' + bootstrapper)

    game = bootstrapper.bootstrap_game(base)
    with game.env:
        _log.debug('Bootstrapping game file system...')
        bootstrapper.bootstrap_filesystem(game.fs)
        bootstrapper.bootstrap_game_filesystem(game)

        # Import all modules to build dependency tree.
        for mod in game.fs.listdir(MODULE_MOUNT):
            if not mod.startswith('__') and (mod.endswith('.py') or game.fs.isdir(mod)):
                __import__(MODULE_PACKAGE + '.' + mod.replace('.py', ''))

    _log('Game bootstrapped.')
    return game


def shutdown_game(game):
    """ Finalize and shut down game. """
    _log('Shutting down game: {}...', game.name)
    with game.env:
        game.fs.clear()

def shutdown():
    """ Finalize and shutdown engine. """
    _log('Shutting down engine...')
    shutdown_game(rave.game.engine)

    _log('Removing hooks...')
    rave.loader.remove_hooks()
