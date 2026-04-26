# Config Design — ErgoConfig

## Current State (v1.0.0)

Config is a module-level `dict` exposed as `from ergolog import config`. It's a `dictConfig` schema that's applied on import via `dictConfig(config)` — but only if the logger has no existing handlers.

Problems with current approach:
- `config` dict is a **dead letter** after import — mutating it does nothing
- Exposes `dictConfig` internals (`ErgoTagFilter`, `ErgoFormatter`, `"()"` tuples)
- No way to reconfigure after import
- If any handler exists on the logger, ergolog silently skips all formatting
- `propagate: True` causes double-printing in app/framework contexts

## New Design: ErgoConfig

### Philosophy

- **Env vars are the emergency brake** — only used to *prevent* auto-configuration
- **Python API is how you configure** — ergonomic, no `dictConfig` schema exposure
- **`dictConfig` is an implementation detail** — users never see it

### Env Vars

| Env var | Purpose |
|---|---|
| `ERGOLOG_NO_COLORS` | Strip ANSI output (current, keep) |
| `ERGOLOG_NO_TIME` | Strip timestamps (current, keep) |
| `ERGOLOG_NO_AUTO_SETUP` | Don't configure any handlers on import |

Three env vars. All negative toggles. All *prevent* something.

`ERGOLOG_FORMAT` and `ERGOLOG_LOG_FILE` are **NOT** needed as env vars — the Python API handles those use cases.

### ErgoConfig API

```python
from ergolog import eg

# Script mode — zero config needed
eg.info("hello")  # auto-configured on import

# Library mode — prevent auto-config, then customize
# ERGOLOG_NO_AUTO_SETUP=1 (or set before import in Python)

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

### `add_output()` signature

```python
eg.config.add_output(kind, path=None, format=None, level=None)
```

- `kind`: `"stdout"` (default), `"file"`, `"stderr"`
- `path`: required when `kind="file"`
- `format`: `"default"` (colored), `"plain"` (no ANSI), `"json"` (JSONL)
- File handler always appends (mode `"a"`)

### Handler composition

| Method | What it does |
|---|---|
| `add_output(kind, ...)` | Adds a handler |
| `remove_output(kind)` | Removes a handler |
| `set_format(format, kind?, path?)` | Changes formatter on a handler |

`set_level()` and `set_propagate()` were removed — use `eg._logger.setLevel()` and `eg._logger.propagate` directly.

### Auto-config behavior

On import, if `ERGOLOG_NO_AUTO_SETUP` is not set and the `ergo` logger has no handlers:
1. Register both `ErgoFormatter` and `ErgoJSONFormatter`
2. Add a `StreamHandler` to stdout with `ErgoFormatter`
3. Attach `ErgoTagFilter` to the handler
4. Set `propagate` based on whether we're in "script mode" or not

### Formatter registration

Both formatters are always registered in the config dict. The handler picks which one to use by name. This means `eg.config.set_format("json")` just changes the formatter reference on the handler — no handler recreation needed.

### Propagation

Default: `propagate=True` (ergolog messages also go to root logger handlers).
Control via `eg._logger.propagate = False` — prevents double-printing in framework contexts.

### Combinations

```python
# Default: pretty colored stdout
from ergolog import eg

# Pretty stdout + JSON file
eg.config.add_output("file", path="app.jsonl", format="json")

# JSON to stdout only (no colors)
eg.config.set_format("json")

# Library in a Flask app — disable auto-config, add structured file output later
# ERGOLOG_NO_AUTO_SETUP=1
eg.config.add_output("file", path="/var/log/app.jsonl", format="json")
```

### What this replaces

- `from ergolog import config` → removed (dead letter)
- `dictConfig` schema → internal implementation detail
- `ErgoTagFilter` / `ErgoFormatter` class references in config → hidden

### Migrating from current API

- `config['formatters']` etc. → `eg.config.add_output()` / `eg.config.set_format()`
- `config['loggers']` level → `eg._logger.setLevel()`
- `config` dict mutation → never worked anyway, now properly unsupported