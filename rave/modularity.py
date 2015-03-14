import heapq
import rave.loader


## Constants.

PRIORITY_MIN = -100
PRIORITY_MAX = 100
PRIORITY_NEUTRAL = 0


## Internals.

_loading_stack = []
_requirements = {}
_provisions = {}
_provided = set()
_available = {}
_initialized = set()


## API.

class ModuleLoader(rave.loader.VFSImporter):
    """
    A loader that loads rave engine modules, taking module initialization, requirements and provisions into account.
    """
    def exec_module(self, module):
        # Register that we're initializing an engine module.
        _loading_stack.append(module)
        try:
            super().exec_module(module)
        finally:
            _loading_stack.pop()

        if _loading_stack:
            # Another engine module tried to this module. Add it as dependency.
            loader = _loading_stack[-1].__name__
            _requirements.setdefault(loader, [])
            _requirements[loader].append(module.__name__)

        register_module(module)


def register_module(module):
    if not hasattr(module, '__priority__'):
        module.__priority__ = PRIORITY_NEUTRAL

    # Store module.
    _available[module.__name__] = module

    # Register provisions.
    if hasattr(module, '__provides__'):
        for provision in module.__provides__:
            _provisions.setdefault(provision, [])
            # Store the id as a 'random number' to make the tuple comparison for the heap queue work
            # because modules objects are not comparable in case of identical priorities.
            heapq.heappush(_provisions[provision], (module.__priority__, id(module), module))

    # Register requirements.
    if hasattr(module, '__requires__'):
        _requirements.setdefault(module.__name__, [])
        _requirements[module.__name__].extend(module.__requires__)

def load_module(mod):
    for dependency in reversed(_resolve_dependencies(mod)):
        init_module(dependency)

    init_module(mod)

def init_module(mod):
    if not _is_initialized(mod):
        if hasattr(mod, 'init'):
            mod.init()
        _mark_initialized(mod)


## Internal API.

def _resolve_dependencies(mod, resolving=None):
    dependencies = []
    if resolving is None:
        resolving = []

    for requirement in _requirements.get(mod.__name__, []):
        if requirement in resolving or _is_provided(requirement):
            continue

        for _, _, provider in _provision_candidates(requirement):
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
    if provision in _available:
        return [provision] + _provisions.get(provision, [])
    return _provisions.get(provision, [])
