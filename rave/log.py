"""
Thin wrapper around Python's (atrocious) logging module.

As a module, use `rave.log.get(__name__)` to get the logger for your module.

`rave.log.Logger` objects have the following API:
- inform(message, *args, **kwargs): log message on INFO level. Message will be formatted using str.format according to the arguments.
- debug(message, *args, **kwargs): log message on DEBUG level. See `inform`.
- warn(message, *args, **kwargs): log message on WARNING level. See `inform`.
- err(message, *args, **kwargs): log message on ERROR level. See `inform`.
- fatal(message, *args, **kwargs): log message on FATAL level. See `inform`.
- exception(exception, message, *args, **kwargs): log exception. See `inform`.

- hook(level, callback): hook any message from logger on given level. Callback will be called with the message level and message as arguments.
- unhook(level, callback): remove previously installed hook.
- file: the file the logger is logging to.
- formatter: the Python logging.Formatter instance associated with this logger.

- FORMAT (static): the default logging format.
- DATE_FORMAT (static): the default format for the date used in the logging format.
- FILE (static): the default logfile.
- LEVEL (static): the level cutoff for which messages will be recorded.
"""
import logging
from . import game


## Internals.

_loggers = {}

class LogFilter(logging.Filter):
    """ Filter that adds current game information to every message. """
    def filter(self, record):
        record.game = game.current() or '<engine>'
        return True


## API.

# Log levels.
EXCEPTION = 0x1
FATAL = 0x2
ERROR = 0x4
WARNING = 0x8
INFO = 0x10
DEBUG = 0x20


class Logger:
    """
    Thin wrapper around Python's rather atrocious logging module in order to make it more bearable.
    Formats messages automatically according to advanced string formatting, handles logger name and logfile changes painlessly.
    """
    FORMAT = '{asctime} [{game}:{name}] {levelname}: {message}'
    DATE_FORMAT = None
    FILE = None
    LEVEL = INFO | WARNING | ERROR | FATAL | EXCEPTION

    def __init__(self, name=None, file=None, level=None, filter=None, formatter=None):
        self._file = file or self.FILE
        self._filter = filter or LogFilter()
        self._formatter = formatter or logging.Formatter(self.FORMAT, datefmt=self.DATE_FORMAT, style='{')
        self._hooks = { FATAL: [], ERROR: [], WARNING: [], INFO: [], DEBUG: [], EXCEPTION: [] }
        self._level = level or self.LEVEL

        if name:
            self._name = name
            self._refresh_logger()

    def _refresh_logger(self):
        """ Recreate logger instance. """
        self.logger = logging.Logger(self.name)
        self._setup_logger()

    def _setup_logger(self):
        """ Set logger settings. """
        self.logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler()
        handler.setFormatter(self.formatter)
        self.logger.addHandler(handler)
        self.logger.addFilter(self.filter)

        if self.file:
            handler = logging.FileHandler(self.file)
            handler.setFormatter(self.formatter)
            self.logger.addHandler(handler)

    def _call_hooks(self, level, message):
        """ Call hooks for `message` at log level `level`. """
        for hook in self._hooks[level]:
            hook(level, message)


    def hook(self, level, callback):
        """
        Hook logger messages at `level` with `callback`.
        The callback will be called for each message at the given level with two arguments:
        - The log level the message applies to.
        - The actual log message.
        """
        self._hooks[level].append(callback)

    def unhook(self, level, callback):
        """ Unhook level with callback. """
        self._hooks[level].remove(callback)

    @property
    def name(self):
        """ This logger's identifier. """
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self._refresh_logger()

    @property
    def file(self):
        """ The file we are logging to, if any. """
        return self._file

    @file.setter
    def file(self, value):
        self._file = value
        self._refresh_logger()

    @property
    def formatter(self):
        """ The formatter we are using. """
        return self._formatter

    @formatter.setter
    def formatter(self, value):
        self._formatter = value
        self._refresh_logger()

    @property
    def filter(self):
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value
        self._refresh_logger()

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value



    def __call__(self, *args, **kwargs):
        return self.inform(*args, **kwargs)

    def debug(self, message, *args, **kwargs):
        """ Log DEBUG message. """
        if self.level & DEBUG:
            message = message.format(*args, **kwargs)
            self.logger.debug(message)
            self._call_hooks(DEBUG, message)

    def inform(self, message, *args, **kwargs):
        """ Log INFO message. """
        if self.level & INFO:
            message = message.format(*args, **kwargs)
            self.logger.info(message)
            self._call_hooks(INFO, message)

    def warn(self, message, *args, **kwargs):
        """ Log WARNING message. """
        if self.level & WARNING:
            message = message.format(*args, **kwargs)
            self.logger.warning(message)
            self._call_hooks(WARNING, message)

    def err(self, message, *args, **kwargs):
        """ Log ERROR message. """
        if self.level & ERROR:
            message = message.format(*args, **kwargs)
            self.logger.error(message)
            self._call_hooks(ERROR, message)

    def fatal(self, message, *args, **kwargs):
        """ Log FATAL message. """
        if self.level & FATAL:
            message = message.format(*args, **kwargs)
            self.logger.fatal(message)
            self._call_hooks(FATAL, message)

    def exception(self, exception, message='', *args, **kwargs):
        """ Log exception. """
        if self.level & EXCEPTION:
            self.logger.exception(exception)
            self._call_hooks(EXCEPTION, message)


def get(name, file=None):
    """ Get logger by module name. """
    if name not in _loggers:
        _loggers[name] = Logger(name, file=file)
    else:
        if file and _loggers[name].file != file:
            _loggers[name].file = file
    return _loggers[name]
