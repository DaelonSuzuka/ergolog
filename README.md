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
[DEBUG   ] ergo (main.py:3) debug
[INFO    ] ergo (main.py:4) info
[WARNING ] ergo (main.py:5) warning
[ERROR   ] ergo (main.py:6) error
[CRITICAL] ergo (main.py:7) critical
```

## Named Loggers

```py
from ergolog import eg

eg('test').debug('named logger')
```

```
[DEBUG   ] ergo.test (main.py:3) named logger
```

Child loggers:

```py
one = eg('one')
two = one('two')

two.info('child logger')
```

```
[INFO    ] ergo.one.two (main.py:4) child logger
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
[INFO    ] ergo [tag1] (main.py:4) one tag
[INFO    ] ergo [tag1, tag2] (main.py:6) two tags
[INFO    ] ergo [tag1] (main.py:7) one tag again
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
[DEBUG   ] ergo (main.py:14) start
[DEBUG   ] ergo [outer] (main.py:9) before
[INFO    ] ergo [outer, inner] (main.py:5) test
[DEBUG   ] ergo [outer] (main.py:12) after
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
[DEBUG   ] ergo [keyword=tags, comma=multiple] (main.py:4) 
[INFO    ] ergo [keyword=tags, comma=multiple, regular tag] (main.py:6) 
[INFO    ] ergo [keyword=tags, comma=multiple, regular tag, more=keywords] (main.py:8)
[DEBUG   ] ergo [keyword=tags, comma=multiple] (main.py:9)
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
[INFO    ] ergo [job=34bfbe] (main.py:4) first
[INFO    ] ergo [job=34bfbe, job=80dbc9] (main.py:6) nested
[INFO    ] ergo [job=34bfbe] (main.py:7) first again
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

Counters are tag values that update live — each log line shows the current value.

### Loop enumeration

```py
loops = eg.counter()
with eg.tag(i=loops):
    for item in loops.count(['a', 'b', 'c']):
        eg.info(f'item {item}')
```

```
[INFO    ] ergo [i=1] (main.py:4) item a
[INFO    ] ergo [i=2] (main.py:4) item b
[INFO    ] ergo [i=3] (main.py:4) item c
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

## Timers

```py
from ergolog import eg

with eg.timer(lambda t: eg.debug(f'took {t}S')):
    eg.info('before')
    # ... do stuff
    eg.info('after')
```

```
[INFO    ] ergo (main.py:4) before
[INFO    ] ergo (main.py:6) after
[DEBUG   ] ergo (main.py:3) took 0.101S
```

Or use as a context manager to capture elapsed time:

```py
with eg.timer() as t:
    # ... do stuff
    pass

eg.debug(f'took {t} S')
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
[WARNING ] ergo [trace=my_function] (ergolog.py:241) registering trace
[DEBUG   ] ergo [trace=my_function] (ergolog.py:252) done in 0.000S
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