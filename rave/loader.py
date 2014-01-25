"""
rave module loader.

This module allows code to install Python import hooks in order to load Python modules from the virtual file system.
These hooks will themselves hook Python's import code to search certain given paths in the VFS for modules in a certain package.
"""
import os
import sys
import imp
import importlib.abc
import importlib.machinery
import importlib.util
import marshal

from . import filesystem, log


## Constants.

SOURCE_ENCODING = 'utf-8'
SOURCE_FALLBACK_ENCODING = 'iso-8859-1'


## Internals.

_installed_finders = []
_log = log.get(__name__)


## Loader classes.

class ModuleLoader(importlib.abc.InspectLoader):
    """ A loader that loads modules from virtual file system. """

    def __init__(self):
        self._modules = {}

    def register(self, name, parent, path, is_package):
        """ Register module as loadable through this loader. """
        self._modules[name] = {
            'path': path,
            'parent': parent,
            'handle': filesystem.open(path),
            'is_package': is_package,
            'source': None,
            'code': None
        }

    def _load_code(self, name):
        """ Load (and optionally compile) module code. """
        data = self._modules[name]

        # Determine how to load code. Do we load from a precompiled Python source?
        if any(data['path'].endswith(ext) for ext in importlib.machinery.BYTECODE_SUFFIXES):
            data['source'] = None
            data['code'] = self._load_compiled(data['handle'])
            _log.debug('Loaded module {name} from bytecode.', name=name)
        # Or do we load from raw Python source?
        elif any(data['path'].endswith(ext) for ext in importlib.machinery.SOURCE_SUFFIXES):
            data['source'], data['code'] = self._load_source(data['handle'], data['path'])
            _log.debug('Loaded module {name} from source.', name=name)
        else:
            raise ImportError('Unsure how to load code from file "{}".'.format(data['path']))

    def _load_compiled(self, handle):
        """ Load code object from compiled file. """
        # .pyc files are very simple: a magic number, a timestamp and marshaled code.
        with handle as f:
            magic = f.read(4)
            time = f.read(4)
            marshaled = f.read()

        # Sanity check.
        if magic != imp.get_magic():
            raise ImportError('This file has been compiled for a different Python version than currently running.')

        # Unmarshal that code.
        return marshal.loads(marshaled)

    def _load_source(self, handle, path):
        """ Load code object from source. """
        # Read code.
        with handle as f:
            source = f.read()

        # Decode code.
        source = self._decode_source(source)
        # Compile code!
        return source, self.source_to_code(source, path)

    def _decode_source(self, source):
        """ Decode binary source to text. """
        # Check if the easier Python 3.4+ API is available first.
        if hasattr(importlib.util, 'decode_source'):
            return importlib.util.decode_source(source)

        # Do the manual way.
        try:
            txt = source.decode(SOURCE_ENCODING)
        except UnicodeDecodeError:
            txt = source.decode(SOURCE_FALLBACK_ENCODING)

        # Windows-style newlines.
        txt = txt.replace('\r\n', '\n')
        # Mac OS9-style newlines.
        txt = txt.replace('\r', '\n')
        # Native newlines.
        txt = txt.replace(os.linesep, '\n')
        return txt

    @importlib.util.module_for_loader
    def load_module(self, module):
        """ Load module. Python 3.3- API for module loading. """
        name = module.__name__
        if name not in self._modules:
            raise ImportError('Incorrect module name for this loader.')
        info = self._modules[name]

        # Set relevant metadata.
        module.__file__ = info['path']
        if info['is_package']:
            module.__path__ = []

        self.exec_module(module)
        return module

    def exec_module(self, module):
        """ Execute module code. Python 3.4+ API for module loading. """
        name = module.__name__
        if name not in self._modules:
            raise ImportError('Incorrect module name for this loader.')
        info = self._modules[name]

        # Only log loading of top-level modules.
        cleaned_name = name.replace(info['parent'], '').strip('.')
        if '.' not in cleaned_name:
            _log('Loading module {name}...', name=name)
        else:
            _log.debug('Loading submodule {name}...', name=name)

        if info['code'] is None:
            self._load_code(name)

        # TODO: Implement execution environments and make this use them.
        exec(info['code'], module.__dict__)

    def is_package(self, name):
        """ Determine whether or not the given module is a package. """
        if name not in self._modules:
            raise ImportError('Incorrect module name for this loader.')
        return self._modules[name]['is_package']

    def get_source(self, name):
        """ Get module source code. """
        if name not in self._modules:
            raise ImportError('Incorrect module name for this loader.')

        if self._modules[name]['code'] is None:
            self._load_code(name)
        return self._modules[name]['source']

    def get_code(self, name):
        """ Get module code. """
        if name not in self._modules:
            raise ImportError('Incorrect module name for this loader.')

        if self._modules[name]['code'] is None:
            self._load_code(name)
        return self._mdules[name]['code']

    def source_to_code(self, source, path):
        """ Compile source code to code. Python 3.4+ API. """
        return compile(source, path, 'exec', dont_inherit=True)

    def module_repr(self, module):
        """ Get representation of module. Python 3.3- API. """
        if module.__name__ not in self._modules:
            raise ImportError('Incorrect module name for this loader.')
        return "<rave module '{}' from '{}'>".format(module.__name__, self._modules[module.__name__]['path'])


class EmptyPackageLoader(importlib.abc.InspectLoader):
    """ A loader that creates empty package modules. """

    def __init__(self):
        self._packages = set()

    def register(self, package):
        """ Register package as loadable through this loader. """
        self._packages.add(package)

    @importlib.util.module_for_loader
    def load_module(self, module):
        """ Load module code. Python 3.3- API for module loading. """
        if module.__name__ not in self._packages:
            raise ImportError('Incorrect module name for this loader.')

        self.exec_module(module)
        return module

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

    def module_repr(self, module):
        """ Get representation of module. Python 3.3- API. """
        if module.__name__ not in self._packages:
            raise ImportError('Incorrect module name for this loader.')
        return "<rave module holder '{}'>".format(module.__name__)


class ModuleFinder(importlib.abc.MetaPathFinder):
    """ A module that attempts to find modules in the virtual file system and pass them to relevant loaders. """
    _loader = ModuleLoader()
    _package_loader = EmptyPackageLoader()

    def __init__(self, search_paths, package):
        self.search_paths = search_paths
        self.package = package
        self._package_loader.register(package)

    def find_module(self, name, path=None):
        """ Find loader for given module. Python 3.3- API. """
        # We only find modules intended for us.
        if name != self.package and not name.startswith(self.package + '.'):
            return None

        # Create empty 'holder' module.
        if name == self.package:
            return self._package_loader

        # Search module path in the virtual file system.
        relpath = name.replace(self.package + '.', '').replace('.', filesystem.PATH_SEPARATOR)
        _log.debug('Got request to find {pkg} in the VFS.', pkg=name)

        for searchpath in self.search_paths:
            basepath = filesystem.join(searchpath, relpath)
            existing = []
            extensions = importlib.machinery.SOURCE_SUFFIXES + importlib.machinery.BYTECODE_SUFFIXES

            # Attempt single-file modules first.
            modpaths = [ basepath + ext for ext in extensions ]
            existing.extend((path, False) for path in modpaths if filesystem.exists(path) and filesystem.isfile(path))
            # Attempt packages.
            packagepaths = [ filesystem.join(basepath, '__init__' + ext) for ext in extensions ]
            existing.extend((path, True) for path in packagepaths if filesystem.exists(path) and filesystem.isfile(path))

            # Get the first one we can load.
            for path, is_package in existing:
                try:
                    self._loader.register(name, self.package, path, is_package)
                    _log.debug('Found {pkg} in {path}. (candidates: {existing})', pkg=name, path=path, existing=[file for file, _ in existing])
                    return self._loader
                except filesystem.FileNotFound:
                    continue

        # Nothing found.
        _log.debug('{pkg} not found in the VFS.', pkg=name)
        return None

    def find_spec(self, name, path=None):
        """ Find ModuleSpec for given module. Python 3.4+ API. """
        loader = self.find_loader(name, path)
        return importlib.util.spec_from_loader(name, loader)

    def __repr__(self):
        return '<rave.loader.ModuleFinder ({})>'.format(self.package)


## API

def install_hook(package, paths):
    """
    Register an import hook for the virtual file system. Returns an identifier that can be passed to `remove_hook`.
    `package` gives the base package this hook should apply to, `paths` the search paths in the VFS the hook should search in.
    """
    finder = ModuleFinder(paths, package)
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
