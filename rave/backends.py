"""
rave backend system.

Backends in rave provide for a way to remove core functionality from rave for certain categories into modules.
An example of reasoning for this would be that tere's a lot of ways you'd implement said functionality given the platform,
for which modules would provide better pluggable functionality.

Any code that uses `register(category, backend)` has to implement the following API:
- BACKEND_PRIORITY: a constant between `PRIORITY_MIN` and `PRIORITY_MAX`, where `PRIORITY_MIN` equals a last resort backend,
    `PRIORITY_NEUTRAL` equals a neutral priority, and `PRIORITY_MAX` equals the most important backend.
- backend_available(category): a function that returns whether or not the backend is available for this platform.
- backend_load(category): a callback called when this module has decided this backend.

Code that needs access to a certain backend can then use `select(category)` ensure a backend is selected for the given category,
and from then on use `rave.backends.<category>` to access the selected backend.
"""
import heapq
import rave.log


## Backend categories.

BACKEND_AUDIO = 1
BACKEND_VIDEO = 2
BACKEND_INPUT = 3

# Backends for which only one choice is appropriate.
SINGLE_BACKEND_CATEGORIES = [ BACKEND_AUDIO, BACKEND_VIDEO ]
# Backend for whuch multiple choices can be loaded at once.
MULTIPLE_BACKEND_CATEGORIES = [ BACKEND_INPUT ]
# All backend categories.
ALL_CATEGORIES = SINGLE_BACKEND_CATEGORIES + MULTIPLE_BACKEND_CATEGORIES
# Backend to strings.
CATEGORY_NAMES = {
    BACKEND_AUDIO: 'audio',
    BACKEND_VIDEO: 'video',
    BACKEND_INPUT: 'input'
}

# Priorities.
PRIORITY_MIN = -100
PRIORITY_MAX = 100
PRIORITY_NEUTRAL = 0


## API.

def register(category, backend):
    """ Register a backend under the given category. """
    if category not in ALL_CATEGORIES:
        raise ValueError('Unknown category: {}'.format(category))

    if not hasattr(backend, 'BACKEND_PRIORITY'):
        backend.BACKEND_PRIORITY = PRIORITY_NEUTRAL

    _candidates.setdefault(category, [])

    # heapq implements a min-priority queue, so adjust priority to match.
    priority = -backend.BACKEND_PRIORITY
    # Order by priority, then by a pseudo-random number to avoid comparison crashing
    # on backends with identical priorities, since modules are not comparable.
    entry = (priority, id(backend), backend)
    heapq.heappush(_candidates[category], entry)

    _log.debug('Registered {cat} backend: {backend}', cat=CATEGORY_NAMES[category], backend=backend.__name__)

def remove(category, backend):
    """ Remove backend as candidate for given category. """
    if category not in ALL_CATEGORIES:
        raise ValueError('Unknown category: {}'.format(category))

    priority = -backend.BACKEND_PRIORITY
    entry = (priority, id(backend), backend)
    _candidates[category].remove(entry)

def select(category):
    """ Select a backend for the given category and load it. """
    if category not in ALL_CATEGORIES:
        raise ValueError('Unknown category: {}'.format(category))

    selected = set()
    if category in _selected:
        selected = _selected[category]
    else:
        for _, _, backend in sorted(_candidates.get(category, [])):
            if _is_available(category, backend) and _load_backend(category, backend):
                _log('Selected {cat} backend: {backend}', cat=CATEGORY_NAMES[category], backend=backend.__name__)

                # Mark as selected.
                _selected.setdefault(category, set())
                _selected[category].add(backend)
                selected.add(backend)

                if category in SINGLE_BACKEND_CATEGORIES:
                    break
        else:
            if not selected:
                _log.err('No {cat} backends available.', cat=CATEGORY_NAMES[category])

    if category in SINGLE_BACKEND_CATEGORIES:
        if not selected:
            return None
        return selected.pop()
    return selected



## Internals.

_candidates = {}
_selected = {}
_log = rave.log.get(__name__)

def _is_available(category, backend):
    if hasattr(backend, 'backend_available'):
        try:
            return backend.backend_available(category)
        except Exception as e:
            _log.debug('Backend {backend} not available: {err}', backend=backend.__name__, err=e)
            return False
    return True

def _load_backend(category, backend):
    if hasattr(backend, 'load_backend'):
        try:
            backend.load_backend(category)
        except Exception as e:
            _log.warn('Error loading backend {backend}: {err}', backend=backend.__name__, err=e)
            return False
        else:
            return True
    return True
