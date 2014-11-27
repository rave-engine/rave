"""
rave filesystem-based bootstrapper.

This will load the FileSystemSource module from the file system and load the modules and games from a normal file system.
"""
import os.path as path
import importlib
import rave.bootstrap
import rave.game
import rave.modularity


MODULES = [ 'filesystemsource' ]
ENGINE_BASE_PATH = path.dirname(path.dirname(path.dirname(__file__)))
ENGINE_PATH = path.join(ENGINE_BASE_PATH, 'rave')
MODULE_PATH = path.join(ENGINE_BASE_PATH, 'modules')
COMMON_PATH = path.join(ENGINE_BASE_PATH, 'common')
GAME_DEFAULT_PATH = path.dirname(ENGINE_BASE_PATH)


def bootstrap_modules():
    # Make sure the engine module package is imported and set the temporay bootstrap import path.
    module_package = importlib.import_module(rave.bootstrap.MODULE_PACKAGE)
    module_package.__path__ = [ MODULE_PATH ]

    # Bootstrap modules.
    for module in MODULES:
        name = rave.bootstrap.MODULE_PACKAGE + '.' + module
        mod = importlib.import_module(name)
        rave.modularity.register_module(mod)
        rave.modularity.load_module(mod)

    # Reset import path.
    module_package.__path__ = []

def bootstrap_filesystem(filesystem):
    """ Bootstrap engine mounts on the file system. """
    import rave.modules.filesystemsource as fss

    # Clear filesystem entirely.
    filesystem.clear()

    # Bootstrap engine mounts.
    filesystem.mount(rave.bootstrap.ENGINE_MOUNT, fss.FileSystemSource(filesystem, ENGINE_PATH))
    filesystem.mount(rave.bootstrap.MODULE_MOUNT, fss.FileSystemSource(filesystem, MODULE_PATH))
    filesystem.mount(rave.bootstrap.COMMON_MOUNT, fss.FileSystemSource(filesystem, COMMON_PATH))

def bootstrap_game(base):
    return rave.game.Game(path.basename(base.rstrip('/\\')), base)

def bootstrap_game_filesystem(game):
    """ Bootstrap the game. """
    import rave.modules.filesystemsource as fss

    # Determine file system locations.
    if game.base:
        game_dir = path.join(game.base, 'game')
        game_module_dir = path.join(game.base, 'modules')

        # Bootstrap game module mount.
        game.fs.mount(rave.bootstrap.GAME_MOUNT, fss.FileSystemSource(game.fs, game_dir))
        game.fs.mount(rave.bootstrap.MODULE_MOUNT, fss.FileSystemSource(game.fs, game_module_dir))
