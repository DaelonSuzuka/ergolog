# ErgoConfig

## Overview

Every `ErgoLog` instance has its own `ErgoConfig`. `eg.config` manages the root logger (`ergo`). `one.config` manages the named child logger (`ergo.one`). Each config targets the stdlib `logging.Logger` that its wrapper wraps.

The common case is a single call at program start on the root logger:

```python
from ergolog import eg

eg.config.add_output('file', path='app.jsonl', format='json')
```

Child loggers inherit root handlers via stdlib propagation by default. Per-logger configuration is available for partitioning specific loggers (e.g. a library module that logs to its own file).

## Philosophy

- Env vars are the emergency brake — only used to prevent auto-configuration
- Python API is how you configure — no `dictConfig` schema exposure to users
- `dictConfig` is an implementation detail

## Env Vars

| Env var | Purpose |
|---|---|
| `ERGOLOG_NO_COLORS` | Strip ANSI output |
| `ERGOLOG_NO_TIME` | Strip timestamps |
| `ERGOLOG_NO_AUTO_SETUP` | Don't configure any handlers on import |

All three are negative toggles: they prevent something.

## API

```python
from ergolog import eg

# Script mode — zero config needed
eg.info("hello")  # auto-configured on import

# Add JSON output to a file on the root logger
eg.config.add_output("file", path="app.jsonl", format="json")

# Add plain (no-color) stdout
eg.config.add_output("stdout", format="plain")

# JSON to stdout
eg.config.set_format("json")

# Remove an output
eg.config.remove_output("file")

# Per-logger: direct output for a named child logger
one = eg('worker')
one.config.add_output('file', path='worker.jsonl', format='json')
```

For log level and propagation, use the standard `logging` API:

```python
import logging
eg._logger.setLevel(logging.WARNING)    # filter by level
eg._logger.propagate = False            # prevent double-logging in frameworks
```

## `add_output()`

```python
eg.config.add_output(kind, path=None, format=None, level=None)
```

- `kind`: `"stdout"`, `"file"`, `"stderr"`
- `path`: required when `kind="file"`
- `format`: `"default"` (colored), `"plain"` (no ANSI), `"json"` (JSONL)
- File handler always appends (mode `"a"`)
- `ErgoTagFilter` is attached to every handler created by `ErgoConfig`

## Handler Lifecycle

| Method | What it does |
|---|---|
| `add_output(kind, ...)` | Adds a handler; replaces existing handler of same kind |
| `remove_output(kind)` | Removes a handler |
| `set_format(format, kind?, path?)` | Changes formatter on a handler |

## Auto-config Behavior

On import, `eg = ErgoLog()` creates `eg.config = ErgoConfig('ergo')` and calls `self.config.auto_setup()`. Auto-setup runs only for the root logger:

1. Skip if `ERGOLOG_NO_AUTO_SETUP` is set
2. Skip if the logger already has handlers
3. Add a `StreamHandler` to stdout with `ErgoFormatter`

Child loggers (`eg('one')`) create their own `ErgoConfig('ergo.one')` but auto-setup is a no-op. They inherit output via standard logging propagation unless configured directly.

## Invariants

- `ErgoConfig.add_output()` creates handlers via Python `logging` API directly, not via `dictConfig` — no destructive reconfiguration
- `ErgoConfig` is created per `ErgoLog` instance; each targets its own wrapped `logging.Logger`
- Auto-setup fires only on root logger (`_logger_name == DEFAULT_LOGGER`)
- Child loggers receive the root config via stdlib `Logger.propagate` by default
- Both formatters are always registered in the internal config dict; `set_format()` swaps the formatter reference on the handler without recreation
- `ErgoTagFilter` is attached to every handler created by `ErgoConfig`

## What This Replaced

- `from ergolog import config` → removed (dead letter)
- `dictConfig` schema → internal implementation detail
- `ErgoTagFilter` / `ErgoFormatter` class references in user config → hidden
