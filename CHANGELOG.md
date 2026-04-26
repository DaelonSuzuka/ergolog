# Changelog

## v1.1.0

### New Features

- **Timer laps** — `t.lap()` returns elapsed as float without stopping; `t.lap('name')` records a named lap for auto-collection by events
- **Timer as tag value** — `with eg.tag(elapsed=t)` shows dynamic elapsed time per log line
- **Counter as event value** — `e.set(processed=counter)` evaluates at emit time, showing the final count
- **Timer as event value** — `e.set(duration=t)` evaluates at emit time, showing final elapsed
- **Named laps auto-collected in events** — named laps on timers set into events are merged into the event context automatically, giving per-stage timing in a single log line
- **`e.warn()`** — sets event level to WARNING; optionally records a warning message and context
- **`ErgoTimer.elapsed`** property — returns current elapsed as float
- **`ErgoTimer.laps`** property — returns dict of named lap times
- **`ErgoTimer.__float__`** and **`__str__`** — timers are now usable as numeric values directly
- **Demo script** (`demo.py`) — self-printing demo with ANSI syntax highlighting via `tokenize`
- **Jupyter notebook** (`demo.ipynb`) — interactive walkthrough of all features

### Bug Fixes

- **`e.warn()` was missing** — the README documented `e.warn()` but it was not implemented; now added

### Tests

- Added `test/test_composition.py` with 20 tests covering timer laps, timer/counter as tag values, timer/counter as event values, named laps in events, and `e.warn()`

---

## v1.0.0

Initial stable release.

### Core Features

- **Single entry point** — `from ergolog import eg`
- **Named/child loggers** — `eg('name')` produces `ergo.name`; `one('two')` produces `ergo.one.two`
- **Tag system** — context-manager and decorator tags with positional and keyword support
- **Callable tag values** — `eg.tag(job=eg.uid)` for auto-generated 6-char hex IDs
- **Counters** — `eg.counter()` as mutable tag values that update per-record; supports `+=`, `-=`, `.count()` for loop enumeration, and accumulation
- **Timers** — `eg.timer()` as context-manager or decorator with optional callback
- **Trace decorator** — `@eg.trace()` logs function entry and timing; `log_args=True` for debug-mode arg/return logging
- **Wide events** — `eg.event()` accumulates context and emits a single log line with duration; supports `e.error()` for error outcomes
- **JSON formatter** — `ErgoJSONFormatter` outputs NDJSON for log aggregation systems

### Architecture

- Thread-safe and async-safe via `contextvars.ContextVar` — each thread/async task sees its own tag stack
- Tags decoupled from formatter via `ErgoTagFilter` — `record.tags` (display) and `record.tag_list` (structured)
- Config dict exposed as `from ergolog import config` — modifiable before setup
- `dictConfig` only fires if no existing handlers — won't stomp on app logging
- Color-coded ANSI output (disable via `ERGOLOG_NO_COLORS`)
- Timestamps optional (disable via `ERGOLOG_NO_TIME`)
- Default logger name overridable via `ERGOLOG_DEFAULT_LOGGER`

### Testing & CI

- Test suite: basic logging, named loggers, tags, counters, timers, trace, exceptions, threading
- GitHub Actions CI across Python 3.9–3.13
- Linted with `ruff` (line-length 120, single quotes)
- Built with `uv`