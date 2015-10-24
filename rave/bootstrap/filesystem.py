"""
rave filesystem-based bootstrapper.

This will load the FileSystemSource module from the file system and load the modules and games from a normal file system.
"""
import os.path as path
import importlib
import rave.bootstrap
import rave.filesystem
import rave.game

MODULES = [ 'filesystemsource' ]
ENGINE_BASE_PATH = path.dirname(path.dirname(path.dirname(__file__)))
ENGINE_PATH = path.join(ENGINE_BASE_PATH, 'rave')
MODULE_PATH = path.join(ENGINE_BASE_PATH, 'modules')
COMMON_PATH = path.join(ENGINE_BASE_PATH, 'common')
GAME_DEFAULT_PATH = path.dirname(ENGINE_BASE_PATH)



def bootstrap_engine(engine):
    # Bootstrap file system source.
    import rave.modules
    rave.modules.__path__ = [ MODULE_PATH ]
    import rave.modules.filesystemsource as fss

    # Clear filesystem.
    engine.fs.clear()
    # Bootstrap engine mounts.
    engine.fs.mount(rave.filesystem.ENGINE_MOUNT, fss.FileSystemSource(ENGINE_PATH))
    engine.fs.mount(rave.filesystem.MODULE_MOUNT, fss.FileSystemSource(MODULE_PATH))
    engine.fs.mount(rave.filesystem.COMMON_MOUNT, fss.FileSystemSource(COMMON_PATH))

    # Remove initial bootstrap.
    rave.modules.__path__.remove(MODULE_PATH)

def bootstrap_game(engine, base):
    import rave.modules.filesystemsource as fss
    name = path.basename(base.rstrip('/\\'))
    game = rave.game.Game(name, base)

    with game.env:
        # Clear filesystem entirely and overlay engine mount.
        game.fs.clear()
        game.fs.mount('/', rave.filesystem.FileSystemProvider(engine.fs))

        # Determine file system locations.
        if game.base:
            gamepath = path.join(game.base, 'game')
            modpath  = path.join(game.base, 'modules')

            # Bootstrap game mounts.
            game.fs.mount(rave.filesystem.GAME_MOUNT, fss.FileSystemSource(gamepath))
            game.fs.mount(rave.filesystem.MODULE_MOUNT, fss.FileSystemSource(modpath))

    return game
