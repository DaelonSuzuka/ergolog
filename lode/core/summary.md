# Core — API & Architecture

## Module Structure

Single-file library: `src/ergolog/ergolog.py` contains all implementation.

```mermaid
classDiagram
    class ErgoLog {
        -_name: str
        -_logger: Logger
        +config: ErgoConfig
        +debug/info/warning/error/critical
        +__call__(name) ErgoLog
        +getLogger(name) ErgoLog
        +tag(*tags, **kwtags) ErgoTagger
        +timer(cb?) ErgoTimer
        +event(**context) ErgoEvent
        +trace(func) wrapper
        +uid() str
        +counter() ErgoCounter
    }
    class ErgoConfig {
        +VALID_FORMATS: tuple
        +VALID_OUTPUTS: tuple
        -_logger_name: str
        -_logger: Logger
        -_tag_filter: ErgoTagFilter
        +add_output(kind, path?, format?, level?)
        +remove_output(kind, path?)
        +set_format(format, kind?, path?)
        +set_level(level)
        +set_propagate(propagate)
        +auto_setup()
    }
    class ErgoTagger {
        _tag_stack_var: ContextVar
        -_tags: list~str~
        -_kwtags: dict
        +applied_tags: List~Union~str, Tuple~str, Any~~
        +__enter__()
        +__exit__()
        +__call__(wrapped) decorator
    }
    class ErgoEvent {
        -_logger: ErgoLog
        -_context: dict
        -_start: float
        -_emitted: bool
        -_error: Exception?
        -_level: int
        +set(**context) ErgoEvent
        +error(err, **context) ErgoEvent
        +warn(message?, **context) ErgoEvent
        +emit(**override) void
        +context: dict (property)
        +duration: float (property)
        +__enter__()
        +__exit__()
    }
    class ErgoCounter {
        -_value: int
        +__iadd__(other)
        +__isub__(other)
        +__repr__() str
        +__eq__(other) bool
        +count(iterable) iterator
    }
    class ErgoTagFilter {
        +filter(record) bool
    }
    class ErgoTimer {
        -start: float
        -cb: Callable
        -_laps: dict~str, float~
        +elapsed: float (property)
        +lap(name?) float
        +laps: dict~str, float~ (property)
        +__repr__() str
        +__str__() str
        +__float__() float
        +__enter__()
        +__exit__()
        +__call__(wrapped) decorator
    }
    class ErgoFormatter {
        +format(record) str
    }
    class ErgoJSONFormatter {
        +format(record) str (JSONL)
    }
    class C {
        +BLACK/RED/GREEN/... ANSI codes
        +dim(text) str
        +apply(text, style) str
    }
    ErgoLog --> ErgoConfig : config
    ErgoLog --> ErgoTagger : creates via .tag()
    ErgoLog --> ErgoTimer : creates via .timer()
    ErgoLog --> ErgoEvent : creates via .event()
    ErgoLog --> ErgoCounter : creates via .counter()
    ErgoTagFilter --> ErgoTagger : reads _tag_stack_var
    ErgoFormatter --> C : uses for styling
    ErgoJSONFormatter --> ErgoEvent : formats event context
    ErgoConfig --> ErgoTagFilter : attaches to handlers
    ErgoConfig --> ErgoFormatter : creates formatters
    ErgoConfig --> ErgoJSONFormatter : creates formatters
```

## Key Behaviors

### Named/Child Loggers
- `eg('name')` → logger `ergo.name`
- `eg('name')('child')` → logger `ergo.name.child`
- `eg()` returns the root logger (cached identity)
- `eg('')` returns identity — `''.removeprefix('ergo.')` produces `''`, fallsthrough to `name = self._name`
- `eg('ergo')` returns identity — exact name match, no `if name != self._name` prefix added
- `eg('ergo.')` returns identity — trailing dot absorbed
- `one('')` returns identity on a named logger
- `one('ergo.one')` returns identity on a named logger
- `one('ergo.one.two')` works — redundant prefix is stripped before qualification
- Loggers are cached in `ErgoLog._loggers`; `__init__` registers `self` to ensure identity

### Config (ErgoConfig)
- `eg.config` is an `ErgoConfig` instance targeting the root logger (`ergo`)
- Each named/child logger also has its own `config` targeting its own wrapped `logging.Logger`
- Auto-setup on import only fires for the root logger; child loggers inherit via stdlib propagation
- `ergo.config.add_output(...)` affects only `ergo`
- `one.config.add_output(...)` affects only `ergo.one`
- File output always uses append mode
- Calling `add_output()` with the same kind replaces the existing handler
- `ErgoTagFilter` is attached to every handler created by `ErgoConfig`
- Both formatters are always available — `set_format('json')` swaps without recreating the handler

### Counter/Accumulator
- `eg.counter()` creates an `ErgoCounter` instance (starts at 0)
- Supports `+=` (increment/accumulate), `-=` (decrement), `==` (comparison to int or other counter)
- `.count(iterable)` wraps iteration and auto-increments each loop
- As a tag kwarg value, evaluated per-record (shows current value on each log line, unlike `eg.uid` which is evaluated once on enter)
- `ErgoCounter` objects are stored as `tuple(key, counter)` on the tag stack; the filter formats them at log time

### Timer
- Can be used as context manager or decorator
- Optional callback receives formatted elapsed string
- `.elapsed` property returns current elapsed time as float
- `.lap()` returns current elapsed as float without stopping the timer
- `.lap('name')` returns elapsed AND records a named lap in `_laps` dict
- `.laps` property returns a (copy) dict of named laps: `{name: elapsed_float}`
- Re-entering a timer context resets `_laps`
- Usable as tag value: `with eg.tag(elapsed=t)` — shows dynamic elapsed per log line (e.g. `[elapsed=0.123s]`)
- Usable as event value: `e.set(duration=t)` — resolves to total elapsed at emit time
- When timer is an event value, its named laps are auto-collected into the event context

### Composability (Events + Counters + Timers)
- Counters and timers passed to `e.set()` are stored by reference, evaluated at emit time
- Counter in event: `e.set(count=counter)` → event shows `counter._value` at emit time
- Timer in event: `e.set(duration=t)` → event shows `t.elapsed` at emit time
- Named laps auto-collected: if timer has `_laps`, they're merged into the event context
- `e.set(fetch=t.lap())` also works for explicit control — `t.lap()` returns a float, not a timer reference
- Explicit lap values (floats) are stored as plain values; they don't trigger auto-lap collection

### Trace Decorator
- Intended for local debugging only; emits a `WARNING` at decoration time as a reminder not to leave it in production code
- Logs function name and timing by default; `@eg.trace(log_args=True)` opts into logging arguments and return values
- `@eg.trace()` requires parens — no bare `@eg.trace`
- Wraps function with both `tag` and `timer`
- Equivalent to `@eg.tag(trace=func.__name__)` + `@eg.timer()`

### JSON Formatter (ErgoJSONFormatter)
- Outputs each log as a JSON object on a single line (JSONL/NDJSON)
- Includes: `timestamp`, `level`, `name`, `message`, `tags`, `event`, `duration_s`, `location`
- For wide events, `event` contains the full accumulated context
- For regular logs, `tags` contains the tag stack as a dict
- Usage: `eg.config.add_output('stdout', format='json')` or `eg.config.set_format('json')`

## Invariants
- `ErgoLog._loggers` key is always the fully-qualified logger name (e.g. `ergo.sub`)
- Tag stacks are context-isolated via `contextvars.ContextVar` — no cross-thread or cross-task leakage
- `set()/reset(token)` ensures tags are always cleaned up on context exit, even on exceptions
- `ErgoTagFilter` must be present on any handler that needs `record.tags` — custom configs must include it
- `ErgoConfig` attaches `ErgoTagFilter` to every handler it creates
- Color output is all-or-nothing per process (env var check at import time)
- `ErgoEvent` emits exactly once; after `emit()` the event is sealed and further `set()` calls are ignored
- Wide events capture tag stack at emit time, not at creation time
- Counters and timers in events are stored by reference and evaluated at emit time (live values)
- Named laps on timers in events are auto-collected into event context at emit time
- `ErgoEvent._context` is a plain dict — events are single-threaded by design (born/populated/emit within one scope)
- `ErgoConfig.add_output()` creates handlers via Python `logging` API directly, not via `dictConfig` — no destructive reconfiguration
- Auto-setup only fires once, and only if the logger has no existing handlers