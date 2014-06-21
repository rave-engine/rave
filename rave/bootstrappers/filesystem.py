# Bootstrap rave from the file system.
import os.path as path
import importlib

from .. import bootstrap, loader

MODULES = [ 'filesystemprovider' ]
ENGINE_BASE_PATH = path.dirname(path.dirname(path.dirname(__file__)))
ENGINE_PATH = path.join(ENGINE_BASE_PATH, 'rave')
MODULE_PATH = path.join(ENGINE_BASE_PATH, 'modules')
COMMON_PATH = path.join(ENGINE_BASE_PATH, 'common')
GAME_DEFAULT_PATH = path.dirname(ENGINE_BASE_PATH)


def bootstrap_modules():
    # Make sure the engine module package is imported and set the temporay bootstrap import path.
    module_package = importlib.import_module(bootstrap.MODULE_PACKAGE)
    module_package.__path__ = [ MODULE_PATH ]

    # Bootstrap modules.
    for module in MODULES:
        name = bootstrap.MODULE_PACKAGE + '.' + module
        importlib.import_module(name)

    # Reset import path.
    module_package.__path__ = []

def bootstrap_filesystem(filesystem):
    """ Bootstrap engine mounts on the file system. """
    import rave.modules.filesystemprovider as fsp

    # Clear filesystem entirely.
    filesystem.clear()

    # Bootstrap engine mounts.
    filesystem.mount(bootstrap.ENGINE_MOUNT, fsp.FileSystemProvider(filesystem, ENGINE_PATH))
    filesystem.mount(bootstrap.MODULE_MOUNT, fsp.FileSystemProvider(filesystem, MODULE_PATH))
    filesystem.mount(bootstrap.COMMON_MOUNT, fsp.FileSystemProvider(filesystem, COMMON_PATH))

def bootstrap_game_filesystem(game):
    """ Bootstrap the game. """
    import rave.modules.filesystemprovider as fsp

    # Determine file system locations.
    game_dir = path.join(game.basedir, 'game')
    game_module_dir = path.join(game.basedir, 'modules')

    # Bootstrap game module mount.
    game.fs.mount(bootstrap.GAME_MOUNT, fsp.FileSystemProvider(game.fs, game_dir))
    game.fs.mount(bootstrap.MODULE_MOUNT, fsp.FileSystemProvider(game.fs, game_module_dir))
