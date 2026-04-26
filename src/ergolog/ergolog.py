from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from time import time
from typing import Any, Callable
from uuid import uuid4

# --------------------------------------------------------------------------- #


NO_COLORS = os.environ.get('ERGOLOG_NO_COLORS', None)
NO_TIME = os.environ.get('ERGOLOG_NO_TIME', None)
DEFAULT_LOGGER = os.environ.get('ERGOLOG_DEFAULT_LOGGER', 'ergo')
NO_AUTO_SETUP = os.environ.get('ERGOLOG_NO_AUTO_SETUP', None)


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
    _tag_stack_var: ContextVar[list] = ContextVar('tag_stack', default=[])

    def __init__(self, *tags: str, **kwtags: str | Callable[[], str] | ErgoCounter | ErgoTimer) -> None:
        self._tags = [*tags]
        self._kwtags = kwtags

        self.applied_tags: list[str | tuple[str, Any]] = []

    def __call__(self, wrapped):
        """decorator"""

        def wrapper(*args, **kwargs):
            with self:
                return wrapped(*args, **kwargs)

        return wrapper

    def __enter__(self, *_):
        self.applied_tags = [*self._tags]

        for k, v in self._kwtags.items():
            if isinstance(v, (ErgoCounter, ErgoTimer)):
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
    """A timer that tracks elapsed wall-clock time.

    Supports named laps for marking stages of an operation.
    Can be used as a context manager, decorator, tag value, or event value.

    Usage:
        # Context manager with laps
        with eg.timer() as t:
            fetch_data()
            t.lap('fetch')       # records named lap, returns elapsed float
            process_data()
            t.lap('process')
            # t.elapsed -> total, t.laps -> {'fetch': 0.123, 'process': 0.456}

        # As tag value (dynamic elapsed per log line)
        t = eg.timer()
        with eg.tag(elapsed=t):
            eg.info('step 1')    # [elapsed=0.100]
            sleep(0.1)
            eg.info('step 2')    # [elapsed=0.200]

        # As event value (elapsed + named laps at emit time)
        with eg.event(op='task') as e:
            t = eg.timer()
            e.set(duration=t)
            fetch_data()
            t.lap('fetch')
            process_data()
            t.lap('process')
    """

    def __init__(self, cb: Callable[[str], None] | None = None) -> None:
        self.start = time()
        self.cb = cb
        self._laps: dict[str, float] = {}

    def __call__(self, wrapped):
        """decorator"""

        def wrapper(*args, **kwargs):
            with self:
                return wrapped(*args, **kwargs)

        return wrapper

    def __repr__(self):
        return f'{self.elapsed:.3f}'

    def __str__(self):
        return f'{self.elapsed:.3f}'

    def __float__(self):
        return self.elapsed

    def __enter__(self, *_):
        self.start = time()
        self._laps = {}
        return self

    def __exit__(self, *_):
        if self.cb is not None:
            self.cb(f'{self.elapsed:.3f}')

    @property
    def elapsed(self) -> float:
        """Current elapsed time in seconds (always fresh)."""
        return time() - self.start

    def lap(self, name: str | None = None) -> float:
        """Return current elapsed time without stopping the timer.

        If a name is given, the lap is recorded and will be included
        in the timer's laps dict, and auto-collected by events.

        Args:
            name: Optional name for this lap (e.g. 'fetch', 'process').

        Returns:
            Elapsed time in seconds as a float.
        """
        elapsed = self.elapsed
        if name is not None:
            self._laps[name] = elapsed
        return elapsed

    @property
    def laps(self) -> dict[str, float]:
        """Dictionary of named lap times (elapsed seconds from start)."""
        return dict(self._laps)


class ErgoEvent:
    """Accumulate context for a wide event log.

    Emits a single log line with all accumulated context + duration.
    Can be used as a context manager (auto-emit on exit) or directly.

    Counters and timers passed to set() are evaluated at emit time,
    showing their live values. Named laps on timers are auto-collected.

    Usage as context manager (auto-emit on exit):
        with eg.event(user='alice') as e:
            e.set(cart={'items': 3, 'total': 9999})
            # On exit: emits one log line with all context + duration

    Usage with counters and timers:
        with eg.event(op='export') as e:
            counter = eg.counter()
            t = eg.timer()
            e.set(pages=counter, duration=t)
            for page in pages:
                process(page)
                counter += 1
                t.lap(f'page_{counter}')
            # Event includes: pages=<final count>, duration=<final elapsed>,
            #                  page_1=<lap1>, page_2=<lap2>, ...

    After emit(), further calls to set() or emit() are ignored.
    """

    def __init__(self, logger: 'ErgoLog', **initial_context) -> None:
        self._logger = logger
        self._context = dict(initial_context)
        self._start = time()
        self._emitted = False
        self._error: Exception | None = None
        self._level: int = logging.INFO

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not self._emitted:
            self._error = exc_val
            self._level = logging.ERROR
        if not self._emitted:
            self.emit()
        return False  # Don't suppress exceptions

    def set(self, **context) -> 'ErgoEvent':
        """Add context to the event. Merges with existing context.

        ErgoCounter and ErgoTimer values are stored by reference and
        evaluated at emit time (showing their current/live values).

        Named laps on timers are auto-collected into the event at emit time.

        Returns self for chaining: e.set(x=1).set(y=2)
        """
        if self._emitted:
            return self
        self._context.update(context)
        return self

    def error(self, error: Exception, **context) -> 'ErgoEvent':
        """Record an error. Sets level to ERROR.

        Returns self for chaining.
        """
        if self._emitted:
            return self
        self._error = error
        self._level = logging.ERROR
        self._context.update(context)
        return self

    def warn(self, message: str | None = None, **context) -> ErgoEvent:
        """Set the event level to WARNING.

        Optionally provide a message and additional context.

        Returns self for chaining.
        """
        if self._emitted:
            return self
        self._level = logging.WARNING
        if message:
            self._context['warning'] = message
        self._context.update(context)
        return self

    @staticmethod
    def _resolve_value(value):
        """Resolve a value at emit time. Counters and timers evaluate live."""
        if isinstance(value, ErgoCounter):
            return value._value
        if isinstance(value, ErgoTimer):
            return value.elapsed
        return value

    def _resolve_context(self) -> dict:
        """Build the final context dict, resolving live values and collecting laps."""
        resolved = {}
        timer_laps = {}

        for key, value in self._context.items():
            if isinstance(value, ErgoTimer):
                resolved[key] = round(value.elapsed, 6)
                # Auto-collect named laps from this timer
                if value._laps:
                    timer_laps.update(value._laps)
            elif isinstance(value, ErgoCounter):
                resolved[key] = value._value
            else:
                resolved[key] = value

        # Merge named laps into context (timer laps take precedence if collision)
        for lap_name, lap_time in timer_laps.items():
            if lap_name not in resolved:
                resolved[lap_name] = round(lap_time, 6)

        return resolved

    def emit(self, **override_context) -> None:
        """Emit the wide event. Seals the event (further calls are no-ops)."""
        if self._emitted:
            return

        self._emitted = True
        duration_s = time() - self._start

        # Resolve live values (counters, timers) and collect laps
        final_context = self._resolve_context()

        # Merge override context (also resolve live values)
        for key, value in override_context.items():
            final_context[key] = self._resolve_value(value)

        # Capture current tag stack if present
        tag_stack = ErgoTagger._tag_stack_var.get()
        if tag_stack:
            tags_dict: dict[str, Any] = {}
            for tag in tag_stack:
                if isinstance(tag, tuple):
                    key, value = tag
                    if isinstance(value, ErgoTimer):
                        tags_dict[key] = f'{value.elapsed:.3f}s'
                    else:
                        tags_dict[key] = str(value)
                elif '=' in tag:
                    key, val = tag.split('=', 1)
                    tags_dict[key] = val
                else:
                    tags_dict[tag] = True
            final_context['tags'] = tags_dict

        # Include duration in the event context
        final_context['duration_s'] = round(duration_s, 6)

        # Build message for default formatter
        parts = []
        if self._error:
            parts.append(f'{self._error.__class__.__name__}: {self._error}')

        # Format context for message
        context_parts = []
        for key, value in final_context.items():
            if key == 'tags' or key == 'duration_s':
                continue  # Tags already shown by formatter, duration at end
            context_parts.append(f'{key}={value}')

        if context_parts:
            parts.append(' '.join(context_parts))

        parts.append(f'duration={duration_s:.3f}s')

        message = ' | '.join(parts)

        # Attach context to the log record
        extra = {
            'event': final_context,
            'duration': duration_s,
        }

        self._logger.log(self._level, message, extra=extra)

    @property
    def context(self) -> dict:
        """Get the current accumulated context (read-only snapshot)."""
        return dict(self._context)

    @property
    def duration(self) -> float:
        """Get elapsed time in seconds since event creation."""
        return time() - self._start


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
    def apply(cls, text: str, style: str | list[str]):
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
                key, value = tag
                if isinstance(value, ErgoTimer):
                    s = f'{key}={value.elapsed:.3f}s'
                else:
                    s = f'{key}={value}'
                tag_strings.append(s)
                tag_list.append(s)
            else:
                tag_strings.append(tag)
                tag_list.append(tag)
        record.tag_list = tag_list  # type: ignore[attr-defined]
        record.tags = f'[{", ".join(tag_strings)}] ' if tag_strings else ''  # type: ignore[attr-defined]
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


class ErgoJSONFormatter(logging.Formatter):
    """Structured JSON formatter for logs.

    Outputs each log as a JSON object on a single line (JSONL/NDJSON).
    Useful for log aggregation systems and agent parsing.

    Includes:
        - timestamp (ISO 8601)
        - level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - name (logger name)
        - message
        - tags (dict of tag key: value)
        - event (wide event context if present)
        - duration (seconds if timed operation)
        - location (file, line, function)

    Add via ErgoConfig:
        eg.config.add_output("file", path="app.jsonl", format="json")
    """

    def __init__(self, fmt=None, datefmt=None, style: str = '%'):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)  # type: ignore[arg-type]

    def format(self, record):
        import json
        from datetime import datetime, timezone

        obj: dict[str, Any] = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }

        # Include tags if present
        tag_list = getattr(record, 'tag_list', None)  # type: ignore[attr-defined]
        if tag_list:
            tags_dict = {}
            for tag in tag_list:
                if '=' in tag:
                    key, val = tag.split('=', 1)
                    tags_dict[key] = val
                else:
                    tags_dict[tag] = True
            obj['tags'] = tags_dict

        # Include event context if present (wide events)
        event = getattr(record, 'event', None)  # type: ignore[attr-defined]
        if event:
            obj['event'] = event

        # Include duration if present (timers/events)
        duration = getattr(record, 'duration', None)  # type: ignore[attr-defined]
        if duration is not None:
            obj['duration_s'] = round(duration, 6)

        # Include error info if present
        if record.exc_info:
            obj['error'] = self.formatException(record.exc_info)

        # Include location
        obj['location'] = {
            'file': record.filename,
            'line': record.lineno,
            'function': record.funcName,
        }

        return json.dumps(obj, separators=(',', ':'))


class ErgoConfig:
    """Runtime configuration for ergolog.

    Provides a clean API for managing logging handlers, formatters, and levels.
    Use eg.config.add_output() to add handlers, eg.config.set_format() to change
    formatters, etc.

    The old module-level config dict is replaced by this class — dictConfig
    internals are no longer exposed.
    """

    VALID_FORMATS = ('default', 'plain', 'json')
    VALID_OUTPUTS = ('stdout', 'stderr', 'file')

    def __init__(self, logger_name: str = DEFAULT_LOGGER):
        self._logger_name = logger_name
        self._logger = logging.getLogger(logger_name)
        self._tag_filter = ErgoTagFilter()

    def _make_formatter(self, format: str) -> logging.Formatter:
        """Create a formatter instance for the given format name."""
        if format == 'json':
            return ErgoJSONFormatter()
        return ErgoFormatter()

    def _make_handler(self, kind: str, format: str = 'default',
                      path: str | None = None,
                      level: str | None = None) -> logging.Handler:
        """Create and configure a logging handler."""
        handler: logging.Handler
        if kind == 'file':
            handler = logging.FileHandler(path or 'ergolog.jsonl', mode='a')
        elif kind == 'stderr':
            handler = logging.StreamHandler(sys.stderr)
        else:
            handler = logging.StreamHandler(sys.stdout)

        handler.setFormatter(self._make_formatter(format))
        handler.addFilter(self._tag_filter)

        if level:
            handler.setLevel(getattr(logging, level.upper()))

        handler._ergolog_name = kind if kind != 'file' else f'file_{path}'  # type: ignore[union-attr]
        handler._ergolog_format = format  # type: ignore[union-attr]
        return handler

    def auto_setup(self) -> None:
        """Apply default configuration if not already configured.

        Called automatically on import for the root logger only.
        Child loggers inherit output via propagation by default.
        Safe to call multiple times — won't duplicate handlers.
        """
        if NO_AUTO_SETUP:
            return
        if self._logger_name != DEFAULT_LOGGER:
            return
        if self._logger.handlers:
            return
        self.add_output('stdout', format='default')

    def add_output(self, kind: str = 'stdout', *, path: str | None = None,
                   format: str = 'default', level: str | None = None) -> None:
        """Add a logging output handler.

        Args:
            kind: Output destination — 'stdout', 'stderr', or 'file'.
            path: File path (required when kind='file').
            format: Formatter — 'default' (colored), 'plain' (no ANSI), or 'json'.
            level: Optional log level for this handler (e.g. 'WARNING').
                   Defaults to the logger's current level.
        """
        if kind not in self.VALID_OUTPUTS:
            raise ValueError(f"Invalid output kind '{kind}'. Must be one of: {self.VALID_OUTPUTS}")
        if format not in self.VALID_FORMATS:
            raise ValueError(f"Invalid format '{format}'. Must be one of: {self.VALID_FORMATS}")

        effective_format = 'default' if format == 'plain' else format

        handler_name = kind if kind != 'file' else f'file_{path}'
        for existing_handler in self._logger.handlers[:]:
            if hasattr(existing_handler, '_ergolog_name') and existing_handler._ergolog_name == handler_name:  # type: ignore[attr-defined]
                existing_handler.close()
                self._logger.removeHandler(existing_handler)

        handler = self._make_handler(kind, format=effective_format, path=path, level=level)
        self._logger.addHandler(handler)

        if not self._logger.level or self._logger.level == logging.NOTSET:
            self._logger.setLevel(logging.DEBUG)

    def remove_output(self, kind: str, *, path: str | None = None) -> None:
        """Remove a logging output handler.

        Args:
            kind: Output kind — 'stdout', 'stderr', or 'file'.
            path: File path (used to identify which file handler when kind='file').
        """
        handler_name = kind if kind != 'file' else f'file_{path}'
        for handler in self._logger.handlers[:]:
            if hasattr(handler, '_ergolog_name') and handler._ergolog_name == handler_name:  # type: ignore[attr-defined]
                handler.close()
                self._logger.removeHandler(handler)
                return

    def set_format(self, format: str, kind: str = 'stdout', path: str | None = None) -> None:
        """Change the formatter on an existing handler.

        Args:
            format: Formatter — 'default' (colored), 'plain' (no ANSI), or 'json'.
            kind: Which output to change — 'stdout', 'stderr', or 'file'.
            path: File path (required when kind='file' to identify which file handler).
        """
        if format not in self.VALID_FORMATS:
            raise ValueError(f"Invalid format '{format}'. Must be one of: {self.VALID_FORMATS}")

        effective_format = 'default' if format == 'plain' else format
        handler_name = kind if kind != 'file' else f'file_{path}'
        for handler in self._logger.handlers:
            if hasattr(handler, '_ergolog_name') and handler._ergolog_name == handler_name:  # type: ignore[attr-defined]
                handler.setFormatter(self._make_formatter(effective_format))
                handler._ergolog_format = effective_format  # type: ignore[attr-defined]
                return


class ErgoLog:
    _loggers: dict[str, 'ErgoLog'] = {}

    def __init__(self, name=DEFAULT_LOGGER) -> None:
        self._name = name
        self._logger = logging.getLogger(name)
        self.config = ErgoConfig(name)

        # Register this wrapper instance so getLogger returns identity.
        # `eg('')` resolves to 'ergo' via the empty-string fallback — without
        # this, it would find `None` in _loggers and allocate a second wrapper.
        if name not in ErgoLog._loggers:
            ErgoLog._loggers[name] = self

        # Auto-configure root logger on first creation
        self.config.auto_setup()

        # avoid the extra function calls from __getattr__
        self.debug = self._logger.debug       # type: ignore[assignment]
        self.info = self._logger.info         # type: ignore[assignment]
        self.warning = self._logger.warning   # type: ignore[assignment]
        self.error = self._logger.error       # type: ignore[assignment]
        self.critical = self._logger.critical # type: ignore[assignment]
        self.log = self._logger.log           # type: ignore[assignment]

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

    def tag(self, *tags: str, **kwargs: str | Callable[[], str] | ErgoCounter | ErgoTimer):
        """apply ergolog tags"""
        return ErgoTagger(*tags, **kwargs)

    def timer(self, cb: Callable[[str], None] | None = None):
        """Create a timer"""
        return ErgoTimer(cb)

    def event(self, **initial_context) -> ErgoEvent:
        """Create a wide event accumulator.

        Accumulates context throughout a scope and emits a single log line.
        Can be used as a context manager (auto-emit on exit) or directly.

        Args:
            **initial_context: Initial context to include in the event.

        Returns:
            ErgoEvent instance.

        Example:
            with eg.event(user='alice') as e:
                e.set(cart={'items': 3})
                # On exit: emits one log line with all context + duration

            # Or manually:
            e = eg.event(user='alice')
            e.set(cart={'items': 3})
            e.emit()
        """
        return ErgoEvent(self, **initial_context)

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

        Intended for local debugging only. A WARNING is emitted at decoration time
        as a reminder not to leave it in production code.

        Use log_args=True to log arguments and return values.
        """
        if func is None:
            return lambda f: self.trace(f, log_args=log_args)

        with self.tag(trace=func.__name__):
            self.warning('registering trace')

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

    from time import sleep

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

    @eg.trace()
    def trace_me(a, b):
        return a + b

    trace_me(2, 2)

    line()

    counter = eg.counter()
    with eg.tag(step=counter):
        eg.info('start')
        counter += 1
        eg.info('middle')
        counter += 1
        eg.info('end')

    line()

    loops = eg.counter()
    with eg.tag(i=loops):
        for item in loops.count(['a', 'b', 'c']):
            eg.info(f'item {item}')

    line()

    # Wide event examples
    print('\n--- Wide Events ---\n')

    # Context manager (auto-emit on exit)
    with eg.event(user='alice', action='checkout') as e:
        e.set(cart={'items': 3, 'total': 9999})
        e.set(payment={'method': 'card'})
        # Auto-emits on exit with duration

    print()  # Spacing

    # Manual emit
    e = eg.event(user='bob', action='search')
    e.set(query='ergonomics', results=42)
    e.emit()

    print()  # Spacing

    # Event with error
    try:
        with eg.event(user='charlie', action='failing_op') as e:
            e.set(step='processing')
            raise ValueError('Something went wrong')
    except ValueError:
        pass  # Exception logged by event exit

    print()  # Spacing

    # Event capturing tags
    with eg.tag(request_id='abc123'):
        with eg.event(operation='tagged_op') as e:
            e.set(extra='data')
            # Tags from context are captured in the event
