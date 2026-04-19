# Terminology

- **eg** — the primary exported singleton (`ErgoLog` instance); the user's entry point to all ergolog functionality
- **ErgoLog** — the core logger class extending `logging.Logger`; manages named/child logger instances and exposes `.tag()`, `.timer()`, `.trace`
- **ErgoTagger** — context-manager/decorator that pushes tags onto a shared `tag_stack`; supports positional tags (`'tag'`), keyword tags (`key='val'`), and auto-UUID `job` tags
- **ErgoTimer** — context-manager/decorator that tracks elapsed wall-clock time via `time.time()`; optionally calls a callback on exit
- **ErgoFormatter** — custom `logging.Formatter` that injects tags, color, and optional timestamps into log records
- **C** — ANSI color/style utility class; all output styling flows through `C.apply()` and `C.dim()`
- **tag_stack** — the per-context list of active tags, stored in `ErgoTagger._tag_stack_var` (a `contextvars.ContextVar`); each thread and async task sees its own isolated stack
- **tag** — a short string label prepended to log messages inside `with eg.tag(...)` or `@eg.tag(...)` blocks
- **kwtags** — keyword-argument tags rendered as `key=value` in the tag bracket
- **job** — a special tag name that auto-generates a 6-char hex UUID (`job=34bfbe`) each time the tag context is entered
- **trace** — decorator that logs function registration, arguments, and return value with timing
- **named logger** — a child logger created via `eg('name')` producing logger names like `ergo.name`
- **child logger** — a nested named logger created from an existing named logger, e.g. `one('two')` → `ergo.one.two`
- **ERGOLOG_NO_COLORS** — env var; when set, disables ANSI color output
- **ERGOLOG_NO_TIME** — env var; when set, suppresses timestamp prefix
- **ERGOLOG_DEFAULT_LOGGER** — env var; overrides the default logger name (default: `'ergo'`)