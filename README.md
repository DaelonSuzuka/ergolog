[![.github/workflows/ci.yml](https://github.com/DaelonSuzuka/ergolog/actions/workflows/ci.yml/badge.svg)](https://github.com/DaelonSuzuka/ergolog/actions/workflows/ci.yml)

# ergolog
A minimal, ergonomic Python logging wrapper

`from ergolog import eg` — one entry point for tags, counters, timers, wide events, and trace. Everything context-scoped, thread-safe, and composable.

- **Named loggers** — `eg('name')`, nested with `one('two')`
- **Tags** — stack and nest for context; keyword tags, callable values, auto-UUIDs
- **Counters** — live-updating tag values; enumerate loops, accumulate totals
- **Timers** — elapsed timing with `.lap()` split times and named laps
- **Wide events** — accumulate context, emit a single line; counters, timers, and laps resolve at emit time
- **Trace** — function-level decorator for timing and entry logging
- **Thread-safe** — tag isolation via `contextvars`

## Why ergolog?

Python's `logging` module works, but its API fights you. Every log line is manual string formatting — you scatter `f'request_id={rid}'` across your code and hope you spelled it the same way each time. Correlating lines across a request means grepping for that same string.

Tags fix this. A `with eg.tag(request_id='abc')` block appends `[request_id=abc]` to every log line inside it — no manual interpolation, no typos, and the tag stack unwinds automatically on exception.

But tags alone aren't enough for operation-level visibility. "Did the payment succeed?" isn't answered by scattered `eg.info` lines — you want a **wide event**: one log line that accumulates everything that happened and emits at the end. Counters, timers, and named laps compose into events naturally — `e.set(duration=t, processed=counter)` resolves at emit time, and `t.lap('fetch')` becomes a field in the event automatically. No manual arithmetic, no forgetting to log the final value.

ergolog won't stomp on your app's logging setup — set `ERGOLOG_NO_AUTO_SETUP=1` and it does nothing on import. And it won't break your threads — tags use `contextvars`, so each thread and async task sees only its own context.

## Installation

```shell
uv add ergolog
# or
pip install ergolog
```

## Basic Usage

```py
from ergolog import eg

eg.debug('debug')
eg.info('info')
eg.warning('warning')
eg.error('error')
eg.critical('critical')
```

```
2025-04-25 15:30:01,234 [DEBUG   ] ergo (main.py:3) debug
2025-04-25 15:30:01,235 [INFO    ] ergo (main.py:4) info
2025-04-25 15:30:01,236 [WARNING ] ergo (main.py:5) warning
2025-04-25 15:30:01,237 [ERROR   ] ergo (main.py:6) error
2025-04-25 15:30:01,238 [CRITICAL] ergo (main.py:7) critical
```

> **Colors:** DEBUG is blue, INFO is green, WARNING is yellow, ERROR is red, CRITICAL is magenta. Timestamps and file locations are dimmed. Set `ERGOLOG_NO_COLORS=1` to disable.

## Named Loggers

```py
from ergolog import eg

eg('test').debug('named logger')
```

```
15:30:01,234 [DEBUG   ] ergo.test (main.py:3) named logger
```

Child loggers:

```py
one = eg('one')
two = one('two')

two.info('child logger')
```

```
15:30:01,235 [INFO    ] ergo.one.two (main.py:4) child logger
```

## Tags

```py
from ergolog import eg

with eg.tag('tag1'):
    eg.info('one tag')
    with eg.tag('tag2'):
        eg.info('two tags')
    eg.info('one tag again')
```

```
15:30:01,235 [INFO    ] ergo [tag1] (main.py:4) one tag
15:30:01,236 [INFO    ] ergo [tag1, tag2] (main.py:6) two tags
15:30:01,237 [INFO    ] ergo [tag1] (main.py:7) one tag again
```

### Tag Decorator

```py
from ergolog import eg

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
```

```
15:30:01,234 [DEBUG   ] ergo (main.py:14) start
15:30:01,235 [DEBUG   ] ergo [outer] (main.py:9) before
15:30:01,236 [INFO    ] ergo [outer, inner] (main.py:5) test
15:30:01,237 [DEBUG   ] ergo [outer] (main.py:12) after
```

### Keyword Tags

```py
from ergolog import eg

with eg.tag(keyword='tags', comma='multiple'):
    eg.debug('')
    with eg.tag('regular tag'):
        eg.info('')
        with eg.tag(more='keywords'):
            eg.info('')
    eg.debug('')
```

```
15:30:01,234 [DEBUG   ] ergo [keyword=tags, comma=multiple] (main.py:4) 
15:30:01,235 [INFO    ] ergo [keyword=tags, comma=multiple, regular tag] (main.py:6) 
15:30:01,236 [INFO    ] ergo [keyword=tags, comma=multiple, regular tag, more=keywords] (main.py:8)
15:30:01,237 [DEBUG   ] ergo [keyword=tags, comma=multiple] (main.py:9)
```

### Auto-generated IDs

```py
from ergolog import eg

with eg.tag(job=eg.uid):
    eg.info('first')
    with eg.tag(job=eg.uid):
        eg.info('nested')
    eg.info('first again')
```

```
15:30:01,235 [INFO    ] ergo [job=34bfbe] (main.py:4) first
15:30:01,236 [INFO    ] ergo [job=34bfbe, job=80dbc9] (main.py:6) nested
15:30:01,237 [INFO    ] ergo [job=34bfbe] (main.py:7) first again
```

Any zero-arg callable works as a tag value — it's evaluated once when the tag context is entered.

## Counters

```py
from ergolog import eg

counter = eg.counter()
with eg.tag(step=counter):
    eg.info('start')       # [step=0]
    counter += 1
    eg.info('middle')      # [step=1]
    counter += 1
    eg.info('end')         # [step=2]
```

```
15:30:01,235 [INFO    ] ergo [step=0] (main.py:4) start
15:30:01,236 [INFO    ] ergo [step=1] (main.py:6) middle
15:30:01,237 [INFO    ] ergo [step=2] (main.py:8) end
```

Counters are tag values that update live — each log line shows the current value.

### Loop enumeration

```py
loops = eg.counter()
with eg.tag(i=loops):
    for item in loops.count(['a', 'b', 'c']):
        eg.info(f'item {item}')
```

```
15:30:01,235 [INFO    ] ergo [i=1] (main.py:4) item a
15:30:01,236 [INFO    ] ergo [i=2] (main.py:4) item b
15:30:01,237 [INFO    ] ergo [i=3] (main.py:4) item c
```

### Accumulation

```py
total = eg.counter()
with eg.tag(bytes=total):
    total += 1024
    eg.info('chunk')       # [bytes=1024]
    total += 512
    eg.info('chunk')       # [bytes=1536]
```

```
15:30:01,235 [INFO    ] ergo [bytes=1024] (main.py:4) chunk
15:30:01,236 [INFO    ] ergo [bytes=1536] (main.py:6) chunk
```

## Timers

```py
from ergolog import eg

with eg.timer(lambda t: eg.debug(f'took {t}S')):
    eg.info('before')
    # ... do stuff
    eg.info('after')
```

```
15:30:01,235 [INFO    ] ergo (main.py:4) before
15:30:01,236 [INFO    ] ergo (main.py:6) after
15:30:01,237 [DEBUG   ] ergo (main.py:3) took 0.101S
```

Or use as a context manager to capture elapsed time:

```py
with eg.timer() as t:
    # ... do stuff
    pass

eg.debug(f'took {t} S')
```

```
15:30:01,235 [DEBUG   ] ergo (main.py:5) took 0.123 S
```

### Laps

Use `.lap()` to take split times without stopping the timer. Returns elapsed seconds as a float:

```py
with eg.timer() as t:
    fetch_data()
    fetch_time = t.lap()      # returns float, timer keeps running
    process_data()
    process_time = t.lap()    # returns float from start
    eg.debug(f'fetch={fetch_time:.3f}s process={process_time:.3f}s total={t.elapsed:.3f}s')
```

```
15:30:01,235 [DEBUG   ] ergo (main.py:6) fetch=0.103s process=0.456s total=0.456s
```

Use `.lap('name')` to record named laps — these are auto-collected by events:

```py
with eg.timer() as t:
    fetch_data()
    t.lap('fetch')       # records lap name + time
    process_data()
    t.lap('process')     # records lap name + time
    # t.laps == {'fetch': 0.103, 'process': 0.456}
```

### Timers as Tag Values

Timers can be used as keyword tag values, showing live elapsed time on each log line:

```py
t = eg.timer()
with eg.tag(elapsed=t):
    eg.info('start')        # [elapsed=0.000s]
    sleep(0.1)
    eg.info('middle')       # [elapsed=0.100s]
    sleep(0.1)
    eg.info('end')           # [elapsed=0.200s]
```

## Trace

```py
from ergolog import eg

@eg.trace()
def my_function(a, b):
    return a + b

my_function(2, 2)
```

```
15:30:01,234 [WARNING ] ergo [trace=my_function] (ergolog.py:241) registering trace
15:30:01,235 [DEBUG   ] ergo [trace=my_function] (ergolog.py:252) done in 0.000S
```

By default, `trace` only logs the function name and timing (safe for production). Use `@eg.trace(log_args=True)` to also log arguments and return values (for local debugging only).

## Configuration

Ergolog auto-configures on import — a single stdout handler with colored output. No setup required.

### Python API

Use `eg.config` to add outputs, change formatters, or control propagation:

```py
from ergolog import eg

# Add JSON output to a file (append mode)
eg.config.add_output('file', path='app.jsonl', format='json')

# Add plain (no-color) output to stderr
eg.config.add_output('stderr', format='plain')

# Switch stdout to JSON
eg.config.set_format('json')

# Change log level
eg.config.set_level('WARNING')

# Prevent double-logging in framework contexts
eg.config.set_propagate(False)

# Remove an output
eg.config.remove_output('stdout')
```

Valid formats: `'default'` (colored), `'plain'` (no ANSI), `'json'` (JSONL).
Valid outputs: `'stdout'`, `'stderr'`, `'file'`.

### Using in a library

If you're building a library that uses ergolog, set `ERGOLOG_NO_AUTO_SETUP=1` before importing. This prevents ergolog from configuring any handlers — your host application owns logging:

```py
import os
os.environ['ERGOLOG_NO_AUTO_SETUP'] = '1'
from ergolog import eg
```

### Environment Variables

All env vars are "emergency brakes" — they *prevent* something:

- `ERGOLOG_NO_AUTO_SETUP` — don't configure any handlers on import
- `ERGOLOG_NO_COLORS` — disable ANSI color output
- `ERGOLOG_NO_TIME` — disable timestamp prefix
- `ERGOLOG_DEFAULT_LOGGER` — override the default logger name (default: `ergo`)

### Structured Logging

Tags are available on `LogRecord` as both `record.tags` (display string) and `record.tag_list` (raw list), so custom formatters can access them for JSON or structured output.

## Wide Events

Wide events accumulate context throughout an operation and emit a **single log line** at the end. Use them to capture operation boundaries — "what happened" rather than "how we got here."

```py
from ergolog import eg

# Context manager (auto-emit on exit)
with eg.event(user='alice', action='checkout') as e:
    e.set(cart={'items': 3, 'total': 9999})
    e.set(payment={'method': 'card'})
    # On exit: emits one log line with all context + duration
```

```
15:30:01,235 [INFO    ] ergo (main.py:4) user=alice action=checkout cart={'items': 3, 'total': 9999} payment={'method': 'card'} | duration=0.234s
```

### Manual Emit

```py
e = eg.event(user='bob')
e.set(action='search', query='ergonomics')
e.emit()
```

```
15:30:01,235 [INFO    ] ergo (main.py:3) user=bob action=search query=ergonomics | duration=0.001s
```

### Outcome Levels

Events default to `INFO`. Use `e.error()` or `e.warn()` to mark the outcome:

```py
# Success → INFO
with eg.event(user='alice') as e:
    process_payment()
# → INFO

# Success with concern → WARNING
with eg.event(user='bob') as e:
    result = process_payment()
    if result.used_fallback:
        e.warn('used fallback payment method')
# → WARNING

# Failure → ERROR
try:
    with eg.event(user='charlie') as e:
        raise ValueError('insufficient funds')
except ValueError:
    pass
# → ERROR: ValueError: insufficient funds | user=charlie | duration=0.002s
```

### Sealed After Emit

Events emit exactly once. After `emit()`, further `set()` calls are ignored:

```py
e = eg.event(user='alice')
e.emit()
e.set(ignored='data')  # Ignored, event is sealed
```

### Capturing Tags

Events capture the current tag stack at emit time:

```py
with eg.tag(request_id='abc123'):
    e = eg.event(operation='tagged')
    e.set(extra='data')
    e.emit()
# Event includes: {'tags': {'request_id': 'abc123'}, 'operation': 'tagged', ...}
```

### Counters in Events

Counters passed to `e.set()` evaluate at emit time — the event shows their final value:

```py
counter = eg.counter()
with eg.event(op='batch') as e:
    e.set(processed=counter)
    for item in items:
        process(item)
        counter += 1
# Event shows: processed=5 (or whatever the final count is)
```

```
15:30:01,235 [INFO    ] ergo (main.py:7) op=batch processed=5 | duration=0.034s
```

### Timers in Events

Timers passed to `e.set()` evaluate at emit time — the event shows total elapsed:

```py
t = eg.timer()
with eg.event(op='export') as e:
    e.set(duration=t)
    export_data()
# Event shows: duration=1.234 (total elapsed)
```

```
15:30:01,235 [INFO    ] ergo (main.py:4) op=export duration=1.234 | duration=1.234s
```

### Named Laps in Events

Named laps on timers are auto-collected into events. This is the killer feature for multi-stage operations:

```py
t = eg.timer()
with eg.event(op='pipeline') as e:
    e.set(duration=t)
    fetch_data()
    t.lap('fetch')
    process_data()
    t.lap('process')
    save_results()
    t.lap('save')
# Event includes: duration=0.789 fetch=0.101 process=0.456 save=0.232
```

```
15:30:01,235 [INFO    ] ergo (main.py:9) op=pipeline duration=0.789 fetch=0.101 process=0.456 save=0.232 | duration=0.789s
```

You can also set lap values explicitly for full control:

```py
with eg.event(op='task') as e:
    t = eg.timer()
    fetch_data()
    e.set(fetch_time=t.lap())
    process_data()
    e.set(process_time=t.lap())
```

```
15:30:01,235 [INFO    ] ergo (main.py:6) op=task fetch_time=0.101 process_time=0.456 | duration=0.456s
```

### When to Use Events vs Regular Logs

| Pattern | Purpose |
|---------|---------|
| Regular logs (`eg.info/debug/warning`) | Trace execution, debug flow |
| Wide events (`eg.event()`) | Capture operation outcome |

Use both together for complete visibility:

```py
with eg.event(operation='export') as e:
    e.set(format='pdf', pages=24)
    eg.debug('starting export')      # How we got here
    export_to_pdf(doc)
    eg.debug('export complete')
    # Event emits: what happened (one line)
```

## JSON Formatter

For structured logging to files or log aggregation systems:

```py
import logging
from ergolog import eg, ErgoJSONFormatter

# Configure JSON output
handler = logging.StreamHandler()
handler.setFormatter(ErgoJSONFormatter())
eg._logger.handlers = [handler]

eg.info('hello', extra={'user': 'alice'})
```

Output (one line per log):

```json
{"timestamp":"2024-01-15T10:23:45.123Z","level":"INFO","name":"ergo","message":"hello","user":"alice","tags":{"request_id":"abc123"},"location":{"file":"main.py","line":4,"function":"<module>"}}
```

For wide events, the full context is included:

```json
{"timestamp":"...","level":"INFO","name":"ergo","message":"user=alice action=checkout ...","event":{"user":"alice","action":"checkout","cart":{"items":3},"duration_s":0.234},"tags":{"request_id":"abc123"}}
```