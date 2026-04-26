# ErgoConfig

## Overview

`eg.config` is the `ErgoConfig` instance that manages log handlers and formatters at runtime. It replaces the old module-level `config` dict, which was a dead letter after import.

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

# Add JSON output to a file
eg.config.add_output("file", path="app.jsonl", format="json")

# Add plain (no-color) stdout
eg.config.add_output("stdout", format="plain")

# JSON to stdout
eg.config.set_format("json")

# Remove an output
eg.config.remove_output("file")
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

On import, if `ERGOLOG_NO_AUTO_SETUP` is not set and the `ergo` logger has no handlers:
1. Register both `ErgoFormatter` and `ErgoJSONFormatter`
2. Add a `StreamHandler` to stdout with `ErgoFormatter`
3. Attach `ErgoTagFilter` to the handler
4. Set `propagate` based on whether we're in "script mode" or not

## Invariants

- `ErgoConfig.add_output()` creates handlers via Python `logging` API directly, not via `dictConfig` — no destructive reconfiguration
- Both formatters are always registered in the internal config dict; `set_format()` swaps the formatter reference on the handler without recreation
- Auto-setup only fires once, and only if the logger has no existing handlers
- `ErgoTagFilter` is attached to every handler created by `ErgoConfig`

## What This Replaced

- `from ergolog import config` → removed (dead letter)
- `dictConfig` schema → internal implementation detail
- `ErgoTagFilter` / `ErgoFormatter` class references in user config → hidden
