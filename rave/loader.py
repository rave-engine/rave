"""
rave module loader.

This module allows code to install Python import hooks in order to load Python modules from the virtual file system.
These hooks will themselves hook Python's import code to search certain given paths in the VFS for modules in a certain package.
"""
import sys
import importlib.abc
import importlib.machinery
import importlib.util

import rave.log
import rave.filesystem
import rave.game


## Internals.

_installed_finders = []
_log = rave.log.get(__name__)


## Loader classes.

class EmptyPackageLoader(importlib.abc.InspectLoader):
    """ A loader that creates empty package modules. """

    def __init__(self):
        self._packages = set()

    def register(self, package):
        """ Register package as loadable through this loader. """
        self._packages.add(package)

    def exec_module(self, module):
        """ Execute module code. Python 3.4+ API for module loading. """
        if module.__name__ not in self._packages:
            raise ImportError('Incorrect module name for this loader.')
        # Ensure it's a package.
        module.__path__ = []

    def is_package(self, name):
        """ Empty packages... are packages. """
        if name not in self._packages:
            raise ImportError('Incorrect module name for this loader.')
        return True

    def get_source(self, name):
        """ Packages don't have source. """
        if name not in self._packages:
            raise ImportError('Incorrect module name for this loader.')
        return None

    def get_code(self, name):
        """ Packages don't have code. """
        if name not in self._packages:
            raise ImportError('Incorrect module name for this loader.')
        return None


class VFSImporter(importlib.abc.MetaPathFinder, importlib.abc.SourceLoader):
    """ A module that attempts to find modules in the virtual file system and loads them. """
    _package_loader = EmptyPackageLoader()

    def __init__(self, search_paths, package):
        self.search_paths = search_paths
        self.package = package
        self._package_loader.register(package)
        self._modules = {}

    def __repr__(self):
        return '<{}.{}: {}.*>'.format(self.__module__, self.__class__.__name__, self.package)

    def find_spec(self, name, path, target=None):
        """ Find ModuleSpec for given module. Attempt to see if module exists, basically. """
        # We only find modules intended for us.
        if name != self.package and not name.startswith(self.package + '.'):
            return None

        if name == self.package:
            # Use empty package holder module.
            loader = self._package_loader
            origin = None
            candidates = []
        else:
            # Do we have a file system to load from?
            game = rave.game.current()
            if not game:
                return None

            # Make relative path and find module.
            rel_path = name.replace(self.package + '.', '').replace('.', game.fs.PATH_SEPARATOR)

            for search_path in self.search_paths:
                base_name = game.fs.join(search_path, rel_path)
                extensions = importlib.machinery.SOURCE_SUFFIXES + importlib.machinery.BYTECODE_SUFFIXES
                available = []

                # Single-file modules.
                candidates = [ base_name + ext for ext in extensions ]
                available.extend(path for path in candidates if game.fs.isfile(path))
                # Packages.
                candidates = [ game.fs.join(base_name, '__init__' + ext) for ext in extensions ]
                available.extend(path for path in candidates if game.fs.isfile(path))

                # Find first available candidate.
                for path in available:
                    self._register_module(game, name, path)

                    loader = self
                    origin = path
                    candidates = available
                    break
                else:
                    # Nothing found.
                    return None

        if origin:
            _log.debug('Loading {pkg} from {path}. (candidates: {available})', pkg=name, path=origin, available=candidates)
        return importlib.machinery.ModuleSpec(name, loader, origin=origin)

    def _register_module(self, game, name, path):
        """ Register module as loadable through this loader. """
        self._modules.setdefault(game, {})
        self._modules[game][name] = path

    def exec_module(self, module):
        # Python's default SourceLoader implementation seems to have a bug where it doesn't
        # set __path__ on modules that would be packages, and thus packages can't actually be
        # used as packages, since the low-level importlib bootstrap code will error out. Set it right.
        game = rave.game.current()
        if game and not hasattr(module, '__path__') and self.is_package(module.__name__):
            module.__path__ = game.fs.dirname(self._modules[game][module.__name__])
        # Python's default SourceLoader also sets __package__ incorrectly if it's a package. Set it right too.
        if self.is_package(module.__name__):
            module.__package__ = module.__name__

        super().exec_module(module)

    def get_filename(self, name):
        game = rave.game.current()
        if not game or game not in self._modules or name not in self._modules[game]:
            raise ImportError('Unknown module for this loader.')
        return self._modules[game][name]

    def get_data(self, path):
        game = rave.game.current()
        if not game:
            raise BrokenPipeError('No game file system to load module from.')
        with game.fs.open(path, 'rb') as f:
            return f.read()

    def set_data(self, path, data):
        game = rave.game.current()
        if not game:
            # Silence errors.
            return

        try:
            with game.fs.open(path, 'wb') as f:
                f.write(data)
        except rave.filesystem.FileSystemError:
            # Silence errors.
            pass

    def path_stats(self, path):
        game = rave.game.current()
        if not game:
            raise BrokenPipeError('No game file system to get module info from.')
        if not game.fs.isfile(path):
            raise FileNotFoundError(path)

        return { 'mtime': 0 }


## API.

def install_hook(package, paths, cls=VFSImporter):
    """
    Register an import hook for the virtual file system. Returns an identifier that can be passed to `remove_hook`.
    `package` gives the base package this hook should apply to, `paths` the search paths in the VFS the hook should search in.
    """
    finder = cls(paths, package)
    sys.meta_path.insert(0, finder)
    _installed_finders.append(finder)

    _log.debug('Installed VFS import hook: {pkg} -> {path}', pkg=package, path=paths)
    return finder

def remove_hook(finder):
    """ Remove previously installed hook. """
    _installed_finders.remove(finder)
    sys.meta_path.remove(finder)

    _log.debug('Removed VFS import hook: {pkg}', pkg=finder.package)

def remove_hooks():
    """ Removed all import hooks. """
    while _installed_finders:
        finder = _installed_finders.pop()
        sys.meta_path.remove(finder)

    _log.debug('Removed all VFS import hooks.')
