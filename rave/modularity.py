import heapq
import rave.loader


## Constants.

PRIORITY_MIN = -100
PRIORITY_MAX = 100
PRIORITY_NEUTRAL = 0


## Internals.

_provisions = {}
_provided = set()
_initialized = set()


## API.

class ModuleLoader(rave.loader.VFSImporter):
    """
    A loader that loads rave engine modules, taking module initialization, requirements and provisions into account.
    """
    def exec_module(self, module):
        super().exec_module(module)
        register_module(module)


def register_module(mod):
    # Record provisions.
    if not hasattr(mod, '__priority__'):
        mod.__priority__ = PRIORITY_NEUTRAL
    if hasattr(mod, '__provides__'):
        for provision in mod.__provides__:
            _provisions.setdefault(provision, [])
            heapq.heappush(_provisions[provision], (mod.__priority__, id(mod), mod))

def load_module(mod):
    for dependency in reversed(_resolve_dependencies(mod)):
        init_module(dependency)

    init_module(mod)

def init_module(mod):
    if not _is_initialized(mod):
        if hasattr(mod, 'init'):
            mod.init()
        _mark_initialized(mod)


def _resolve_dependencies(mod, resolving=None):
    dependencies = []
    if resolving is None:
        resolving = []

    for requirement in getattr(mod, '__requires__', []):
        if requirement in resolving or _is_provided(requirement):
            continue

        resolving.append(requirement)
        for priority, _, provider in _provision_candidates(requirement):
            old_resolving = resolving[:]
            try:
                subdependencies = _resolve_dependencies(provider, resolving)

                dependencies.append(provider)
                for dependency in subdependencies:
                    if dependency not in dependencies:
                        dependencies.append(dependency)
            except ImportError:
                resolving = old_resolving
            else:
                _mark_provided(requirement)
                break
        else:
            raise ImportError('Could not resolve dependency "{}" for module "{}".'.format(requirement, mod.__name__))

    return dependencies

def _is_initialized(module):
    return module in _initialized

def _mark_initialized(module):
    _initialized.add(module)

def _is_provided(provision):
    return provision in _provided

def _mark_provided(provision):
    _provided.add(provision)

def _provision_candidates(provision):
    return _provisions.get(provision, [])