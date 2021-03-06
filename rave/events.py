"""
rave event bus.
"""
import rave.log

_log = rave.log.get(__name__)


class StopProcessing(BaseException):
    """ Exception raised to indicate this event should not be processed further. """
    pass

class HookContext:
    def __init__(self, bus, event, handler):
        self.bus = bus
        self.event = event
        self.handler = handler

    def __enter__(self):
        self.bus.hook(self.event, self.handler)
        return self

    def __exit__(self, exctype, excval, exctb):
        self.bus.unhook(self.event, self.handler)

class EventBus:
    def __init__(self):
        self.handlers = {}

    def hook(self, event, handler=None):
        if not handler:
            def do_hook(f):
                self.hook(event, f)
                return f
            return do_hook

        self.handlers.setdefault(event, [])
        self.handlers[event].append(handler)

    def hook_first(self, event, handler=None):
        if not handler:
            def do_hook(f):
                self.hook_first(event, f)
                return f
            return do_hook

        self.handlers.setdefault(event, [])
        self.handlers[event].insert(0, handler)

    def unhook(self, event, handler):
        self.handlers[event].remove(handler)

    def hooked(self, event, handler):
        return HookContext(self, event, handler)

    def emit(self, event, *args, **kwargs):
        handlers = self.handlers.get(event)
        if handlers:
            for handler in handlers:
                try:
                    self._invoke_handler(handler, event, args, kwargs)
                except StopProcessing:
                    break
                except Exception as e:
                    _log.exception(e, 'Exception thrown while processing event {event}.', event=event)


    def _invoke_handler(self, handler, event, args, kwargs):
        handler(event, *args, **kwargs)


## Stateful API.

def current():
    """ Get current event bus. """
    import rave.game, rave.engine
    game = rave.game.current()
    if not game:
        return rave.engine.engine.events
    return game.events

def emit(event, *args, **kwargs):
    return current().emit(event, *args, **kwargs)

def hook(event, handler=None):
    return current().hook(event, handler)

def hook_first(event, handler=None):
    return current().hook_first(event, handler)

def unhook(event, handler):
    return current().unhook(event, handler)
