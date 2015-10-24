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
        """ Execute module code. """
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
        _log.trace('Got import request for: {}', name)

        # We only find modules intended for us.
        if name != self.package and not name.startswith(self.package + '.'):
            return None

        if name == self.package:
            # Use empty package holder module.
            loader = self._package_loader
            origin = None
            package = True
            candidates = []
        else:
            # Do we have a file system to load from?
            fs = rave.filesystem.current()
            if not fs:
                return None

            # Make relative path and find module.
            rel_path = name.replace(self.package + '.', '').replace('.', rave.filesystem.PATH_SEPARATOR)

            for search_path in self.search_paths:
                base_name = fs.join(search_path, rel_path)
                extensions = importlib.machinery.SOURCE_SUFFIXES + importlib.machinery.BYTECODE_SUFFIXES
                available = []

                # Single-file modules.
                candidates = [ base_name + ext for ext in extensions ]
                available.extend(path for path in candidates if fs.isfile(path))
                # Packages.
                candidates = [ fs.join(base_name, '__init__' + ext) for ext in extensions ]
                available.extend(path for path in candidates if fs.isfile(path))

                # Find first available candidate.
                for path in available:
                    self._register_module(fs, name, path)

                    loader = self
                    origin = path
                    package = path.rsplit('.', 1)[0].endswith('__init__')
                    candidates = available
                    break
                else:
                    # Nothing found.
                    return None

        if origin:
            _log.debug('Loading {pkg} from {path}. (candidates: {available})', pkg=name, path=origin, available=candidates)
        return importlib.machinery.ModuleSpec(name, loader, origin=origin, is_package=package)

    def _register_module(self, fs, name, path):
        """ Register module as loadable through this loader. """
        self._modules.setdefault(fs, {})
        self._modules[fs][name] = path

    def get_filename(self, name):
        fs = rave.filesystem.current()
        if fs not in self._modules or name not in self._modules[fs]:
            raise ImportError('Unknown module for this loader.')
        return self._modules[fs][name]

    def get_data(self, path):
        fs = rave.filesystem.current()
        with fs.open(path, 'rb') as f:
            return f.read()

    def set_data(self, path, data):
        fs = rave.filesystem.current()
        if not fs:
            # Silence errors.
            return

        try:
            with fs.open(path, 'wb') as f:
                f.write(data)
        except rave.filesystem.FileSystemError:
            # Silence errors.
            pass

    def path_stats(self, path):
        fs = rave.filesystem.current()
        if not fs.isfile(path):
            raise FileNotFoundError(path)

        return { 'mtime': 0 }


## API.

def install_hook(package, paths, loader=VFSImporter):
    """
    Register an import hook for the virtual file system. Returns an identifier that can be passed to `remove_hook`.
    `package` gives the base package this hook should apply to, `paths` the search paths in the VFS the hook should search in.
    """
    finder = loader(paths, package)
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
