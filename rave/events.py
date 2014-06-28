"""
rave event bus.
"""


## API.

class EventBus:
    def __init__(self):
        self.handlers = {}

    def hook(self, event, handler):
        self.handlers.setdefault(event, [])
        self.handlers[event].append(handler)

    def unhook(self, event, handler):
        self.handlers[event].remove(handler)

    def emit(self, event, *args, **kwargs):
        handlers = self.handlers.get(event)
        if handlers:
            for handler in handlers:
                self._invoke_handler(handler, event, args, kwargs)

    def _invoke_handler(self, handler, event, args, kwargs):
        handler(event, *args, **kwargs)


## Engine event bus.

engine = EventBus()
