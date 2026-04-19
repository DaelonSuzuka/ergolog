import logging
import os
from contextvars import ContextVar
from logging.config import dictConfig
from time import time
from typing import Callable, Optional, Union
from uuid import uuid4

# --------------------------------------------------------------------------- #


NO_COLORS = os.environ.get('ERGOLOG_NO_COLORS', None)
NO_TIME = os.environ.get('ERGOLOG_NO_TIME', None)
DEFAULT_LOGGER = os.environ.get('ERGOLOG_DEFAULT_LOGGER', 'ergo')


# --------------------------------------------------------------------------- #


class ErgoCounter:
    """A mutable counter/accumulator that can be used as a tag value.

    Starts at 0. Supports += for accumulation and .count() for loop enumeration.
    When used as a tag kwarg value, it shows its current value on each log line.
    """

    def __init__(self):
        self._value = 0

    def __iadd__(self, other):
        self._value += other
        return self

    def __isub__(self, other):
        self._value -= other
        return self

    def __repr__(self):
        return str(self._value)

    def __str__(self):
        return str(self._value)

    def __eq__(self, other):
        if isinstance(other, ErgoCounter):
            return self._value == other._value
        return self._value == other

    def count(self, iterable):
        """Iterate over an iterable, incrementing the counter each iteration."""
        for item in iterable:
            self._value += 1
            yield item


class ErgoTagger:
    _tag_stack_var: ContextVar[list[str]] = ContextVar('tag_stack', default=[])

    def __init__(self, *tags: str, **kwtags: Union[str, Callable[[], str]]) -> None:
        self._tags = [*tags]
        self._kwtags = kwtags

        self.applied_tags = []

    def __call__(self, wrapped):
        """decorator"""

        def wrapper(*args, **kwargs):
            with self:
                return wrapped(*args, **kwargs)

        return wrapper

    def __enter__(self, *_):
        self.applied_tags = [*self._tags]

        for k, v in self._kwtags.items():
            if isinstance(v, ErgoCounter):
                self.applied_tags.append((k, v))
            else:
                self.applied_tags.append(f'{k}={v()}' if callable(v) else f'{k}={v}')

        current = self._tag_stack_var.get()
        new_stack = current + self.applied_tags
        self._token = self._tag_stack_var.set(new_stack)

        return self

    def __exit__(self, *_):
        self._tag_stack_var.reset(self._token)
        self.applied_tags = []


class ErgoTimer:
    def __init__(self, cb: Optional[Callable[[str], None]]) -> None:
        self.start = time()
        self.cb = cb

    def __call__(self, wrapped):
        """decorator"""

        def wrapper(*args, **kwargs):
            with self:
                return wrapped(*args, **kwargs)

        return wrapper

    def __repr__(self):
        return f'{time() - self.start:.3f}'

    def __enter__(self, *_):
        self.start = time()
        return self

    def __exit__(self, *_):
        if self.cb is not None:
            self.cb(f'{time() - self.start:.3f}')


# --------------------------------------------------------------------------- #


class C:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    DIM = '\033[2m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'
    OFF = '\033[0m'

    @classmethod
    def dim(cls, text: str):
        if NO_COLORS:
            return text
        return C.DIM + text + C.OFF

    @classmethod
    def apply(cls, text: str, style: Union[str, list[str]]):
        if NO_COLORS:
            return text
        if isinstance(style, list):
            style = ''.join(style)
        return style + text + C.OFF


class ErgoTagFilter(logging.Filter):
    def filter(self, record):
        stack = ErgoTagger._tag_stack_var.get()
        tag_strings = []
        tag_list = []
        for tag in stack:
            if isinstance(tag, tuple):
                key, counter = tag
                s = f'{key}={counter}'
                tag_strings.append(s)
                tag_list.append(s)
            else:
                tag_strings.append(tag)
                tag_list.append(tag)
        record.tag_list = tag_list
        record.tags = f'[{", ".join(tag_strings)}] ' if tag_strings else ''
        return True


class ErgoFormatter(logging.Formatter):
    _time = '' if NO_TIME else C.dim('%(asctime)s ')
    _meta = C.dim(' %(name)s') + ' %(tags)s' + C.dim('(%(filename)s:%(lineno)d) ')

    FORMATS = {
        10: _time + C.apply('[DEBUG   ]', C.BLUE) + _meta + '%(message)s',
        20: _time + C.apply('[INFO    ]', C.GREEN) + _meta + '%(message)s',
        30: _time + C.apply('[WARNING ]', C.YELLOW) + _meta + '%(message)s',
        40: _time + C.apply('[ERROR   ]', C.RED) + _meta + '%(message)s',
        50: _time + C.apply('[CRITICAL]', C.MAGENTA) + _meta + '%(message)s',
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, '')
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


config = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'tags': {
            '()': ErgoTagFilter,
        },
    },
    'formatters': {
        'default': {
            '()': ErgoFormatter,
        },
    },
    'handlers': {
        'default': {
            'filters': ['tags'],
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        }
    },
    'loggers': {
        DEFAULT_LOGGER: {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

if not logging.getLogger(DEFAULT_LOGGER).handlers:
    dictConfig(config)


# *************************************************************************** #


class ErgoLog(logging.Logger):
    _loggers: dict[str, 'ErgoLog'] = {}

    def __init__(self, name=DEFAULT_LOGGER) -> None:
        self._name = name
        self._logger = logging.getLogger(name)

        # avoid the extra function calls from __getattr__
        self.debug = self._logger.debug
        self.info = self._logger.info
        self.warning = self._logger.warning
        self.error = self._logger.error
        self.critical = self._logger.critical

    def __getattr__(self, name: str):
        try:
            return self._logger.__getattribute__(name)
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' and its wrapped logger have no attribute '{name}'") from None

    def __call__(self, name=DEFAULT_LOGGER) -> 'ErgoLog':
        return self.getLogger(name)

    def getLogger(self, name: str) -> 'ErgoLog':
        """get a named logger"""
        name = name.removeprefix(f'{self._name}.')
        if name == '':
            name = self._name
        if name != self._name:
            name = f'{self._name}.' + name

        if name not in ErgoLog._loggers:
            ErgoLog._loggers[name] = ErgoLog(name)

        return ErgoLog._loggers[name]

    def tag(self, *tags: str, **kwargs: Union[str, Callable[[], str]]):
        """apply ergolog tags"""
        return ErgoTagger(*tags, **kwargs)

    def timer(self, cb: Optional[Callable[[str], None]] = None):
        """Create a timer"""
        return ErgoTimer(cb)

    @staticmethod
    def uid():
        """Generate a short unique ID (6-char hex) for use as a callable tag value"""
        return uuid4().hex[:6]

    @staticmethod
    def counter():
        """Create a mutable counter/accumulator for use as a tag value"""
        return ErgoCounter()

    def trace(self, func=None, *, log_args=False):
        """Trace a function — logs entry, timing, and optionally args/return values.

        By default, only logs function name and timing (safe for production).
        Use log_args=True to log arguments and return values (for local debugging only).
        """
        if func is None:
            return lambda f: self.trace(f, log_args=log_args)

        with self.tag(trace=func.__name__):
            self.debug('registering trace')

        def wrapper(*args, **kwargs):
            with self.tag(trace=func.__name__):
                if log_args:
                    self.debug(f'executing {args} {kwargs}')
                with self.timer() as t:
                    result = func(*args, **kwargs)
                if log_args:
                    self.debug(f'done in {t}S returned: {result}')
                else:
                    self.debug(f'done in {t}S')

            return result

        return wrapper


eg = ErgoLog()


# *************************************************************************** #


if __name__ == '__main__':

    def line():
        print('-' * 100)

    line()

    eg.debug('debug')
    eg.info('info')
    eg.warning('warning')
    eg.error('error')
    eg.critical('critical')

    line()

    log = eg('named_logger')
    log.debug('debug')
    log.info('info')
    log.warning('warning')
    log.error('error')
    log.critical('critical')

    line()

    eg.info('')
    one = eg('one')
    one.info('')

    two = one('two')
    two.info('')

    line()

    with eg.tag('with_tag'):
        eg.info('one tag')
        with eg.tag('and'):
            eg.info('two tags')
            with eg.tag('more_tags'):
                eg.info('three tags')
    line()

    with eg.tag(keyword='tags', comma='multiple'):
        eg.debug('')
        with eg.tag('regular_tag'):
            eg.info('')
            with eg.tag(more='keywords'):
                eg.info('')
        eg.debug('')

    from time import sleep

    line()

    @eg.tag('inner')
    def inner():
        eg.info('test')

    @eg.tag('outer')
    def outer():
        eg.debug('before')
        inner()

        eg.debug('after')

    eg.debug('start')
    outer()
    eg.debug('end')

    line()

    @eg.tag(job=eg.uid)
    def inner_job():
        eg.info('inner job')

    @eg.tag(job=eg.uid)
    def outer_job():
        eg.info('outer job')
        inner_job()
        inner_job()

    outer_job()

    line()

    with eg.timer(lambda t: eg.debug(f'took {t}S')):
        eg.info('before')
        sleep(0.1)
        eg.info('after')

    line()

    with eg.timer() as t:
        eg.info('before')
        sleep(0.15)
        eg.info('after')

    eg.debug(f'took {t} S')

    line()

    @eg.timer(lambda t: eg.debug(f'took {t}S'))
    def time_me():
        sleep(0.1)
        eg.info('inside')

    time_me()

    line()

    @eg.trace(log_args=True)
    def trace_me(a, b):
        return a + b

    trace_me(2, 2)
