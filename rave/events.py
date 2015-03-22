"""
rave event bus.
"""
import rave.log


## API.

class StopProcessing(BaseException):
    """ Exception raised to indicate this event should onot be processed further. """
    pass

class EventBus:
    def __init__(self):
        self.handlers = {}

    def hook(self, event, handler):
        self.handlers.setdefault(event, [])
        self.handlers[event].append(handler)

    def hook_first(self, event, handler):
        self.handlers.setdefault(event, [])
        self.handlers[event].insert(0, handler)

    def unhook(self, event, handler):
        self.handlers[event].remove(handler)

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

def current():
    """ Get current event bus. """
    # Prevent circular imports.
    import rave.game
    game = rave.game.current()
    if not game:
        return None
    return game.events


## Internals.

_log = rave.log.get(__name__)
