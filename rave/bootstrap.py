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
from rave import filesystem, loader, log

ENGINE_MOUNT = '/.rave'
ENGINE_PACKAGE = 'rave'
MODULE_MOUNT = '/.modules'
MODULE_PACKAGE = 'rave.modules'
GAME_MOUNT = '/'
GAME_PACKAGE = 'rave.game'
COMMON_MOUNT = '/.common'


## Internal.

_log = log.get(__name__)

def _find_engine_bootstrapper():
    """ Determine the bootstrapper to use for bootstrapping the engine parts. """
    # We currently only have one bootstrapper.
    return 'filesystem'

def _find_game_bootstrapper():
    """ Determine the bootstrapper to use for bootstrapping the game. """
    # We still only have one bootstrapper.
    return 'filesystem'


## API.

def bootstrap_engine(bootstrapper=None):
    """ Bootstrap the engine. """
    _log('Installing import hooks...')
    loader.install_hook(ENGINE_PACKAGE, [ ENGINE_MOUNT ])
    loader.install_hook(MODULE_PACKAGE, [ MODULE_MOUNT ])

    if not bootstrapper:
        bootstrapper = _find_engine_bootstrapper()

    _log('Bootstrapping engine using "{bs}" bootstrapper.', bs=bootstrapper)
    bootstrapper = importlib.import_module('rave.bootstrappers.' + bootstrapper)

    # Bootstrap vital engine modules.
    _log('Bootstrapping engine modules...')
    bootstrapper.bootstrap_modules()
    # Bootstrap file system and mount vital parts.
    _log('Bootstrapping file system...')
    bootstrapper.bootstrap_filesystem()

def bootstrap_game(bootstrapper=None, base=None):
    """ Bootstrap the game with `base` as game base. """
    # Clear out existing game finders.
    loader.install_hook(GAME_PACKAGE, [ GAME_MOUNT ])

    if not bootstrapper:
        bootstrapper = _find_game_bootstrapper()
    bootstrapper = importlib.import_module('rave.bootstrappers.' + bootstrapper)

    bootstrapper.bootstrap_game_filesystem(base)
