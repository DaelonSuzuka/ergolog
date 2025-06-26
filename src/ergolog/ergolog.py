import logging
import os
from logging.config import dictConfig
from time import time
from typing import Callable, Optional, Union
from uuid import uuid4

# --------------------------------------------------------------------------- #


NO_COLORS = os.environ.get('ERGOLOG_NO_COLORS', None)
NO_TIME = os.environ.get('ERGOLOG_NO_TIME', None)
DEFAULT_LOGGER = os.environ.get('ERGOLOG_DEFAULT_LOGGER', 'ergo')


# --------------------------------------------------------------------------- #


class ErgoTagger:
    tag_stack: list[str] = []

    def __init__(self, *tags: str, **kwtags: str) -> None:
        self._tags = [*tags]

        for k, v in kwtags.items():
            self._tags.append(f'{k}={v}')

        self.applied_tags = []

    def __call__(self, wrapped):
        """decorator"""

        def wrapper(*args, **kwargs):
            with self:
                return wrapped(*args, **kwargs)

        return wrapper

    def __enter__(self, *_):
        self.applied_tags = []

        for tag in self._tags:
            if tag == 'job':
                tag = 'job=' + uuid4().hex[:6]

            self.applied_tags.append(tag)

        for tag in self.applied_tags:
            ErgoTagger.tag_stack.append(tag)

        return self

    def __exit__(self, *_):
        for tag in self.applied_tags:
            ErgoTagger.tag_stack.remove(tag)

        self.applied_tags = []


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

    if NO_COLORS:

        @classmethod
        def dim(cls, text: str):
            return text

        @classmethod
        def apply(cls, text: str, style: Union[str, list[str]]):
            return text
    else:

        @classmethod
        def dim(cls, text: str):
            return C.DIM + text + C.OFF

        @classmethod
        def apply(cls, text: str, style: Union[str, list[str]]):
            if isinstance(style, list):
                style = ''.join(style)
            return style + text + C.OFF


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

        record.tags = f'[{", ".join(ErgoTagger.tag_stack)}] ' if ErgoTagger.tag_stack else ''
        return formatter.format(record)


config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            '()': ErgoFormatter,
        },
    },
    'handlers': {
        'default': {
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

dictConfig(config)


# *************************************************************************** #


class ErgoTimer:
    def __init__(self, cb: Optional[Callable[[str], None]]) -> None:
        self.start = time()
        self.cb = cb

    def __repr__(self):
        return f'{time() - self.start:.2f}'

    def __enter__(self, *_):
        return self

    def __exit__(self, *_):
        if self.cb is not None:
            self.cb(f'{time() - self.start:.2f}')


class ErgoLog(logging.Logger):
    _loggers: dict[str, logging.Logger] = {}

    def __init__(self) -> None:
        self._logger = self.__call__()

    def __getattr__(self, name: str):
        return self._logger.__getattribute__(name)

    def __call__(self, name=DEFAULT_LOGGER) -> logging.Logger:
        return self.getLogger(name)

    def getLogger(self, name=DEFAULT_LOGGER) -> logging.Logger:
        """get a named logger"""
        name = name.removeprefix(f'{DEFAULT_LOGGER}.')
        if name == '':
            name = DEFAULT_LOGGER
        if name != DEFAULT_LOGGER:
            name = f'{DEFAULT_LOGGER}.' + name

        if name not in ErgoLog._loggers:
            ErgoLog._loggers[name] = logging.getLogger(name)

        return ErgoLog._loggers[name]

    def tag(self, *tags: str, **kwargs: str):
        """apply ergolog tags

        ```
        # Use as a decorator:
        @eg.tag('tag')
            def func():
                eg.info('inside')
        # Or as context manager:
        with eg.tag('with_tag'):
            eg.info('one tag')
            with eg.tag('and'):
                eg.info('two tags')
        ```

        """
        return ErgoTagger(*tags, **kwargs)

    def timer(self, cb: Optional[Callable[[str], None]] = None):
        return ErgoTimer(cb)

    def trace(self):
        pass


eg = ErgoLog()


# *************************************************************************** #


if __name__ == '__main__':

    def line():
        print('-' * 100)

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

    @eg.tag('job')
    def inner_job():
        eg.info('inner job')

    @eg.tag('job')
    def outer_job():
        eg.info('outer job')
        inner_job()
        inner_job()

    outer_job()

    line()

    a = eg('a')
    with eg.tag('A'), eg.timer(lambda t: a.debug(f'took {t} S')):
        a.info('before')
        sleep(0.5)
        a.info('after')

    line()

    b = eg('b')
    with eg.tag('B'), eg.timer() as t:
        b.info('before')
        sleep(0.5)
        b.info('after')

    b.debug(f'took {t} S')
