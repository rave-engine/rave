import heapq
import rave.log
import rave.loader


## Constants.

PRIORITY_MIN = -100
PRIORITY_MAX = 100
PRIORITY_NEUTRAL = 0


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


def load_all():
    for module in _available:
        try:
            load_module(module)
        except Exception as e:
            _log.exception(e, 'Could not load module {}.', module)

def load_module(name):
    module = _available[name]
    blacklist = {}

    if module in _loaded:
        return

    _log('Loading module: {}', name)
    while True:
        loaded = []
        provisions = {}
        dependencies = _resolve_dependencies(module, blacklist=blacklist.copy(), provided=provisions)

        for dependency in reversed(dependencies):
            if dependency in _loaded:
                continue

            _log.debug('Loading module: {} (dependency)', dependency.__name__)
            try:
                init_module(dependency, provisions)
                loaded.append(dependency)
            except Exception as e:
                blacklist[dependency] = 'initialization failed: {}'.format(e)
                _log.warn('Loading dependency failed, unloading and re-generating dependencies...')

                # Unload all loaded dependencies.
                for dependency in reversed(loaded):
                    _log.trace('Unloading module: {} (dependency)', dependency.__name__)
                    exit_module(dependency)
                # Go back to start of while-loop by breaking out of for-loop.
                break
        else:
            # All dependencies loaded successfully.
            break

    _log.debug('Loading module: {} (main)', module.__name__)
    try:
        init_module(module, provisions)
    except:
        _log.err('Loading failed, unloading dependencies...')
        # Unload all loaded dependencies.
        for dependency in reversed(loaded):
            _log.trace('Unloading module: {} (dependency)', dependency.__name__)
            exit_module(dependency)

        raise

def init_module(module, provisions):
    if module not in _loaded:
        if hasattr(module, 'load'):
            # Filter out provisions requested by module.
            requirements = getattr(module, '__requires__', [])
            provisions = { k: v for k, v in provisions.items() if k in requirements }

            module.load(**provisions)
        _loaded.add(module)

def exit_module(module):
    if module in _loaded:
        if hasattr(module, 'unload'):
            module.unload()
        _loaded.remove(module)


## Internals.

_log = rave.log.get(__name__)
_loading_stack = []
_requirements = {}
_provisions = {}
_available = {}
_loaded = set()


def _resolve_dependencies(mod, resolving=None, provided=None, blacklist=None):
    dependencies = []
    if resolving is None:
        resolving = set()
    if provided is None:
        provided = {}
    if blacklist is None:
        blacklist = {}

    for requirement in _requirements.get(mod.__name__, []):
        # Don't bother with stuff we already handled.
        if requirement in resolving or requirement in provided:
            continue
        resolving.add(requirement)

        errors = []
        for _, _, provider in _provision_candidates_for(requirement):
            if provider in blacklist:
                errors.append('"{}" candidate "{}" is blacklisted ({})'.format(requirement, provider.__name__, blacklist[provider]))
                continue

            # Invocations add to the resolving set since it's pass-by-reference, which is undesired if the resolve ends up failing.
            old_resolving = resolving.copy()
            old_provided = provided.copy()
            try:
                subdependencies = _resolve_dependencies(provider, resolving, provided, blacklist)
            except ImportError as e:
                blacklist[provider] = 'import failed: {}'.format(e)
                errors.append(e)
                # Restore progress from earlier.
                resolving = old_resolving
                provided = old_provided
            else:
                # Add winning candidate to the list, and its dependencies.
                dependencies.append(provider)
                for dependency in subdependencies:
                    # Move dependency to the back if needed, so it will get loaded earlier.
                    if dependency in dependencies:
                        dependencies.remove(dependency)
                    dependencies.append(dependency)

                provided[requirement] = provider
                break
        else:
            # Build useful error message.
            msg = 'Could not resolve dependency "{}" for module "{}": no viable candidates.'.format(requirement, mod.__name__)
            for error in errors:
                for message in str(error).splitlines():
                    msg += '\n   {}'.format(message)
            raise ImportError(msg)

    return dependencies

def _provision_candidates_for(provision):
    # If we are directly referring to a module, put that at the front.
    if provision in _available:
        return [(0, 0, _available[provision])] + sorted(_provisions.get(provision, []))
    return sorted(_provisions.get(provision, []))
