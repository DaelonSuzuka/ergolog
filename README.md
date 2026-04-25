[![.github/workflows/ci.yml](https://github.com/DaelonSuzuka/ergolog/actions/workflows/ci.yml/badge.svg)](https://github.com/DaelonSuzuka/ergolog/actions/workflows/ci.yml)

# ergolog
A minimal, ergonomic python logging wrapper

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

The config dict is exposed for customization before ergolog sets up:

```py
from ergolog import eg, config

config['loggers']['ergo']['level'] = 'WARNING'

from ergolog import eg  # import after modifying config
```

Ergolog only configures logging if the default logger has no existing handlers, so it won't stomp on your application's logging setup.

### Environment Variables

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