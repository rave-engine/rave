"""
Common base elements.
"""
import warnings
import types
from functools import wraps

# rave is stylized, yo.
class raveError(Exception):
    """ Base class for any exception that happens in the rave engine. """
    pass

# Deprecated stuff.
def deprecated(replacement=None):
    """ Deprecate functionality. Calling this function or instantiating this class will issue a warning. """
    if not isinstance(replacement, str):
        replacement = replacement.__qualname__

    def inner(f):
        nonlocal replacement

        # Format message.
        message = '{f} is deprecated and may be removed in future releases.'.format(f=f.__qualname__)
        if replacement:
            message += ' Use {repl} instead.'.format(repl=replacement)
        warn = DeprecationWarning(message)

        # Function?
        if isinstance(f, types.FunctionType):
            @wraps(f)
            def wrapper(*args, **kwargs):
                warnings.warn(warn, stacklevel=2)
                return f(*args, **kwargs)

            return wrapper
        # Class?
        else:
            initializer = f.__init__

            @wraps(initializer)
            def wrapper(*args, **kwargs):
                warnings.warn(warn, stacklevel=2)
                return initializer(*args, **kwargs)

            f.__init__ = wrapper
            return f

    return inner
