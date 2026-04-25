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

2025-04-25 15:30:01,234 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:3)</span> debug  
2025-04-25 15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:4)</span> info  
2025-04-25 15:30:01,236 <span style="color: #f39c12">**[WARNING&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:5)</span> warning  
2025-04-25 15:30:01,237 <span style="color: #e74c3c">**[ERROR&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:6)</span> error  
2025-04-25 15:30:01,238 <span style="color: #9b59b6">**[CRITICAL]**</span> <span style="color: #7f8c8d">ergo (main.py:7)</span> critical

## Named Loggers

```py
from ergolog import eg

eg('test').debug('named logger')
```

15:30:01,234 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo.test (main.py:3)</span> named logger

Child loggers:

```py
one = eg('one')
two = one('two')

two.info('child logger')
```

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo.one.two (main.py:4)</span> child logger

## Tags

```py
from ergolog import eg

with eg.tag('tag1'):
    eg.info('one tag')
    with eg.tag('tag2'):
        eg.info('two tags')
    eg.info('one tag again')
```

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [tag1] <span style="color: #7f8c8d">(main.py:4)</span> one tag  
15:30:01,236 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [tag1, tag2] <span style="color: #7f8c8d">(main.py:6)</span> two tags  
15:30:01,237 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [tag1] <span style="color: #7f8c8d">(main.py:7)</span> one tag again

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

15:30:01,234 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:14)</span> start  
15:30:01,235 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [outer] <span style="color: #7f8c8d">(main.py:9)</span> before  
15:30:01,236 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [outer, inner] <span style="color: #7f8c8d">(main.py:5)</span> test  
15:30:01,237 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [outer] <span style="color: #7f8c8d">(main.py:12)</span> after

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

15:30:01,234 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [keyword=tags, comma=multiple] <span style="color: #7f8c8d">(main.py:4)</span>  
15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [keyword=tags, comma=multiple, regular tag] <span style="color: #7f8c8d">(main.py:6)</span>  
15:30:01,236 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [keyword=tags, comma=multiple, regular tag, more=keywords] <span style="color: #7f8c8d">(main.py:8)</span>  
15:30:01,237 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [keyword=tags, comma=multiple] <span style="color: #7f8c8d">(main.py:9)</span>

### Auto-generated IDs

```py
from ergolog import eg

with eg.tag(job=eg.uid):
    eg.info('first')
    with eg.tag(job=eg.uid):
        eg.info('nested')
    eg.info('first again')
```

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [job=34bfbe] <span style="color: #7f8c8d">(main.py:4)</span> first  
15:30:01,236 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [job=34bfbe, job=80dbc9] <span style="color: #7f8c8d">(main.py:6)</span> nested  
15:30:01,237 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [job=34bfbe] <span style="color: #7f8c8d">(main.py:7)</span> first again

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

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [step=0] <span style="color: #7f8c8d">(main.py:4)</span> start  
15:30:01,236 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [step=1] <span style="color: #7f8c8d">(main.py:6)</span> middle  
15:30:01,237 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [step=2] <span style="color: #7f8c8d">(main.py:8)</span> end

Counters are tag values that update live — each log line shows the current value.

### Loop enumeration

```py
loops = eg.counter()
with eg.tag(i=loops):
    for item in loops.count(['a', 'b', 'c']):
        eg.info(f'item {item}')
```

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [i=1] <span style="color: #7f8c8d">(main.py:4)</span> item a  
15:30:01,236 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [i=2] <span style="color: #7f8c8d">(main.py:4)</span> item b  
15:30:01,237 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [i=3] <span style="color: #7f8c8d">(main.py:4)</span> item c

### Accumulation

```py
total = eg.counter()
with eg.tag(bytes=total):
    total += 1024
    eg.info('chunk')       # [bytes=1024]
    total += 512
    eg.info('chunk')       # [bytes=1536]
```

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [bytes=1024] <span style="color: #7f8c8d">(main.py:4)</span> chunk  
15:30:01,236 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [bytes=1536] <span style="color: #7f8c8d">(main.py:6)</span> chunk

## Timers

```py
from ergolog import eg

with eg.timer(lambda t: eg.debug(f'took {t}S')):
    eg.info('before')
    # ... do stuff
    eg.info('after')
```

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:4)</span> before  
15:30:01,236 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:6)</span> after  
15:30:01,237 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:3)</span> took 0.101S

Or use as a context manager to capture elapsed time:

```py
with eg.timer() as t:
    # ... do stuff
    pass

eg.debug(f'took {t} S')
```

15:30:01,235 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:5)</span> took 0.123 S

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

15:30:01,235 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:6)</span> fetch=0.103s process=0.456s total=0.456s

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

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [elapsed=0.000s] <span style="color: #7f8c8d">(main.py:4)</span> start  
15:30:01,335 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [elapsed=0.100s] <span style="color: #7f8c8d">(main.py:6)</span> middle  
15:30:01,435 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [elapsed=0.200s] <span style="color: #7f8c8d">(main.py:8)</span> end

## Trace

```py
from ergolog import eg

@eg.trace()
def my_function(a, b):
    return a + b

my_function(2, 2)
```

15:30:01,234 <span style="color: #f39c12">**[WARNING&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [trace=my_function] <span style="color: #7f8c8d">(ergolog.py:241)</span> registering trace  
15:30:01,235 <span style="color: #3498db">**[DEBUG&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo</span> [trace=my_function] <span style="color: #7f8c8d">(ergolog.py:252)</span> done in 0.000S

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

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:4)</span> user=alice action=checkout cart={'items': 3, 'total': 9999} payment={'method': 'card'} | <span style="color: #7f8c8d">duration=0.234s</span>

### Manual Emit

```py
e = eg.event(user='bob')
e.set(action='search', query='ergonomics')
e.emit()
```

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:3)</span> user=bob action=search query=ergonomics | <span style="color: #7f8c8d">duration=0.001s</span>

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

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:7)</span> op=batch processed=5 | <span style="color: #7f8c8d">duration=0.034s</span>

### Timers in Events

Timers passed to `e.set()` evaluate at emit time — the event shows total elapsed:

```py
t = eg.timer()
with eg.event(op='export') as e:
    e.set(duration=t)
    export_data()
# Event shows: duration=1.234 (total elapsed)
```

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:4)</span> op=export duration=1.234 | <span style="color: #7f8c8d">duration=1.234s</span>

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

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:9)</span> op=pipeline duration=0.789 fetch=0.101 process=0.456 save=0.232 | <span style="color: #7f8c8d">duration=0.789s</span>

You can also set lap values explicitly for full control:

```py
with eg.event(op='task') as e:
    t = eg.timer()
    fetch_data()
    e.set(fetch_time=t.lap())
    process_data()
    e.set(process_time=t.lap())
```

15:30:01,235 <span style="color: #27ae60">**[INFO&nbsp;&nbsp;&nbsp;&nbsp;]**</span> <span style="color: #7f8c8d">ergo (main.py:6)</span> op=task fetch_time=0.101 process_time=0.456 | <span style="color: #7f8c8d">duration=0.456s</span>

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