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
import rave.log
import rave.loader
import rave.filesystem
import rave.modularity
import rave.engine
import rave.game

_log = rave.log.get(__name__)


def _find_engine_bootstrapper():
    """ Determine the bootstrapper to use for bootstrapping the engine parts. """
    # We currently only have one bootstrapper.
    return 'filesystem'

def _find_game_bootstrapper(base):
    """ Determine the bootstrapper to use for bootstrapping the game. """
    # We still only have one bootstrapper.
    return 'filesystem'

def _load_all_modules():
    """ Import all modules to build dependency tree. """
    for mod in rave.filesystem.listdir(rave.filesystem.MODULE_MOUNT):
        path = rave.filesystem.join(rave.filesystem.MODULE_MOUNT, mod)
        if not mod.startswith('__') and (mod.endswith('.py') or rave.filesystem.isdir(path)):
            try:
                __import__(rave.modularity.MODULE_PACKAGE + '.' + mod.replace('.py', ''))
            except Exception as e:
                _log.exception(e, "Could not import module: {}", mod)



def bootstrap_engine(bootstrapper=None):
    """ Bootstrap the engine. """
    _log('This is rave v{ver}.', ver=__version__)
    engine = rave.engine.Engine()
    rave.engine.engine = engine

    _log.debug('Bootstrapping loader...')
    rave.loader.install_hook(rave.modularity.ENGINE_PACKAGE, [ rave.filesystem.ENGINE_MOUNT ])
    rave.loader.install_hook(rave.modularity.MODULE_PACKAGE, [ rave.filesystem.MODULE_MOUNT ], loader=rave.modularity.ModuleLoader)
    rave.loader.install_hook(rave.modularity.GAME_PACKAGE, [ rave.filesystem.GAME_MOUNT ])

    if not bootstrapper:
        bootstrapper = _find_engine_bootstrapper()
    _log('Selected engine bootstrapper: {name}', name=bootstrapper)

    _log.debug('Bootstrapping engine...')
    bootstrapper = importlib.import_module('rave.bootstrap.' + bootstrapper)
    bootstrapper.bootstrap_engine(engine)
    _load_all_modules()

    _log('Engine bootstrapped.')
    return engine


def bootstrap_game(engine, bootstrapper=None, base=None):
    """ Bootstrap the game with `base` as game base. """
    if not bootstrapper:
        bootstrapper = _find_game_bootstrapper(base)

    _log('Selected game bootstrapper: {name}', name=bootstrapper)
    bootstrapper = importlib.import_module('rave.bootstrap.' + bootstrapper)

    game = bootstrapper.bootstrap_game(engine, base)
    with game.env:
        _load_all_modules()

    _log('Game bootstrapped: {}', game.name)
    return game
