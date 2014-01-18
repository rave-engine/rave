"""
Thin wrapper around Python's (atrocious) logging module.
"""
import logging


## Internals.

_loggers = {}


## API

# Log levels.
EXCEPTION = logging.FATAL + 10
FATAL = logging.FATAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG


class Logger:
    """
    Thin wrapper around Python's rather atrocious logging module in order to make it more bearable.
    Formats messages automatically according to advanced string formatting, handles logger name and logfile changes painlessly.
    """
    FORMAT = '{asctime} [{name}] {levelname}: {message}'
    DATE_FORMAT = None
    FILE = None
    LEVEL = logging.WARNING

    def __init__(self, name=None, file=None, formatter=None):
        self._file = file or self.FILE
        self._formatter = formatter or logging.Formatter(self.FORMAT, datefmt=self.DATE_FORMAT, style='{')
        self._hooks = { FATAL: [], ERROR: [], WARNING: [], INFO: [], DEBUG: [] }
        if name:
            self._name = name
            self._refresh_logger()

    def _refresh_logger(self):
        """ Recreate logger instance. """
        self.logger = logging.Logger(self.name)
        self._setup_logger()

    def _setup_logger(self):
        """ Set logger settings. """
        self.logger.setLevel(self.LEVEL)

        handler = logging.StreamHandler()
        handler.setFormatter(self.formatter)
        self.logger.addHandler(handler)

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


    def __call__(self, *args, **kwargs):
        return self.inform(*args, **kwargs)

    def debug(self, message, *args, **kwargs):
        """ Log DEBUG message. """
        message = message.format(*args, **kwargs)
        self.logger.debug(message)
        self._call_hooks(DEBUG, message)

    def inform(self, message, *args, **kwargs):
        """ Log INFO message. """
        message = message.format(*args, **kwargs)
        self.logger.info(message)
        self._call_hooks(INFO, message)

    def warn(self, message, *args, **kwargs):
        """ Log WARNING message. """
        message = message.format(*args, **kwargs)
        self.logger.debug(message)
        self._call_hooks(WARNING, message)

    def err(self, message, *args, **kwargs):
        """ Log ERROR message. """
        message = message.format(*args, **kwargs)
        self.logger.debug(message)
        self._call_hooks(ERROR, message)

    def fatal(self, message, *args, **kwargs):
        """ Log FATAL message. """
        message = message.format(*args, **kwargs)
        self.logger.debug(message)
        self._call_hooks(FATAL, message)

    def exception(self, exception):
        """ Log exception. """
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