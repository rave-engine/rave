"""
rave backend system.

Backends in rave provide for a way to remove core functionality from rave for certain categories into modules.
An example of reasoning for this would be that tere's a lot of ways you'd implement said functionality given the platform,
for which modules would provide better pluggable functionality.

Any code that uses `register(category, backend)` has to implement the following API:
- PRIORITY: a constant between `PRIORITY_MIN` and `PRIORITY_MAX`, where `PRIORITY_MIN` equals a last resort backend,
    `PRIORITY_NEUTRAL` equals a neutral priority, and `PRIORITY_MAX` equals the most important backend.
- available(): a function that returns whether or not the backend is available for this platform.
- load(): a callback called when this module has decided this backend.

Code that needs access to a certain backend can then use `select(category)` ensure a backend is selected for the given category,
and from then on use `rave.backends.<category>` to access the selected backend.
"""
import sys
import heapq
from rave import log

## Constants.

PRIORITY_MIN = -100
PRIORITY_MAX = 100
PRIORITY_NEUTRAL = 0


## Internal variables.

_log = log.get(__name__)
_available_backends = {}
_selected_backends = {}


## Internal functions.

def _insert_backend(category, backend):
    """ Insert backend into internal structure for category. """
    if category not in _available_backends:
        _available_backends[category] = []

    # Adjust priority so that an ascending sort (as specified by heapq) will yield highest-priority backends.
    adjusted_priority = PRIORITY_MAX - (backend.PRIORITY + PRIORITY_MIN)
    heapq.heappush(_available_backends[category], (adjusted_priority, id(backend), backend))

def _backends_for(category):
    """ Yield a list of sorted backends for category. """
    # Easily enough, the use of heapq makes sure it's already sorted.
    return (backend for priority, id, backend in _available_backends.get(category, []))

def _backend_available(backend):
    """ Determine if the backend is available for this platform. """
    try:
        return backend.available()
    except:
        # TODO: Log?
        return False

def _mark_selected_backend(category, backend):
    """ Mark given backend as selected backend for category. """
    _selected_backends[category] = backend

def _has_selected_backend(category):
    """ Determine if given category has a selected backend. """
    return category in _selected_backends

def _selected_backend(category):
    """ Get selected backend for category. """
    return _selected_backends[category]

def _select_backend(category, backend):
    """
    Attempt to select backend for category. Will return whether or not selection failed.
    Assumes backend is valid for category and available on current platform.
    Returns whether or not selection succeeded.
    """
    try:
        loaded = backend.load()
    except Exception as e:
        _log.exception(e, 'Selected {cat} backend {backend} but load() threw an exception.', backend=backend.__name__, cat=category)
        return False

    if loaded:
        _mark_selected_backend(category, backend)
        setattr(sys.modules[__name__], category, backend)
    else:
        _log.warn('Selected {cat} backend {backend} but load() failed.', backend=backend.__name__, cat=category)

    return loaded


## API.

def register(category, backend):
    """
    Register the given backend module in `category`. Every backend is expected to implement the following API:
    - PRIORITY: constant indicating the backend priority on a scale from `PRIORITY_MIN` to `PRIORITY_MAX`;
        `PRIORITY_MAX` being very important, `PRIORITY_NEUTRAL` neutral, `PRIORITY_MIN` last resort.
    - available(): check if the backend is available on the current platform.
    - load(): the backend has been selected to be loaded. Initialize it.
    """
    priority = backend.PRIORITY
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValueError('Priority for backend {backend} has to lie between {min} and {max}'.format(backend=backend.__name__, min=PRIORITY_MIN, max=PRIORITY_MAX))

    _insert_backend(category, backend)
    _log.debug('Registered {cat} backend: {backend}', cat=category, backend=backend.__name__)

def select(category):
    """
    Select a backend for the given `category`.
    Return the selected backend if it can find a suitable backend, else returns None.
    """
    _log.debug('Selecting {cat} backend...', cat=category)

    if not _has_selected_backend(category):
        # Iterate through sorted list and find a proper backend.
        for backend in _backends_for(category):
            available = _backend_available(backend)
            _log.debug('{backend} available: {av}', backend=backend.__name__, av=available)

            if available:
                if _select_backend(category, backend):
                    break
                else:
                    _log.warn('{backend} available but initialization failed. Moving on.', backend=backend.__name__)
        else:
            _log.err('No {cat} backends available.', cat=category)
            return None

    _log('Selected {cat} backend: {backend}', cat=category, backend=backend.__name__)
    return _selected_backend(category)
