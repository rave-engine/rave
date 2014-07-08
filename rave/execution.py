"""
rave Python execution environments.
"""
import threading
import types

import rave.log


## Internals.

_log = rave.log.get(__name__)
_lock = threading.Lock()
_current_envs = {}

def _identifier():
    """ Get unique identifier for all possible parallel mechanisms. """
    return threading.current_thread().ident


## API.

def current():
    """ Get current execution environment object for whatever parallel mechanism is used, or None if no environment is active. """
    with _lock:
        id = _identifier()

        envs = _current_envs.get(id)
        if envs:
            return envs[-1]
        return None

def push(env):
    """ Set current execution environment for whatever parallel mechanism is used. """
    with _lock:
        id = _identifier()

        _current_envs.setdefault(id, [])
        _current_envs[id].append(env)

def pop():
    """ Clear the current execution environment for whatever parallel mechanism is used. """
    with _lock:
        id = _identifier()

        envs = _current_envs.get(id)
        if envs:
            return envs.pop()
        raise ValueError('No environment to clear.')


## Execution environment.

class ExecutionEnvironment:

    def __init__(self, game=None):
        self.game = game
        self.apis = {}
        self.globals = {}
        self.locals = {}

    def __enter__(self):
        push(self)
        return self

    def __exit__(self, exctype, excval, exctb):
        pop()

    def __repr__(self):
        return '<{} for game {!r}>'.format(self.__class__.__qualname__, self.game)

    def compile(self, code, filename='<unknown>'):
        """ Compile code for use in this environment. """
        return compile(code, 'exec', filename, dont_inherit=True, optimize=2)

    def run(self, code, filename='<unknown>'):
        """ Run code in this environment. """
        with environment(self.env):
            if not isinstance(code, types.CodeType):
                code = self.compile(code, filename)

            exec(code, self.globals, self.locals)

    def run_file(self, filename):
        """ Run file system file in this environment. """
        with self.game.fs.open(filename) as f:
            code = f.read()

        return self.run(code, filename)

    def register_api(self, name, api):
        self.apis[name] = api
