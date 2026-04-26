# Lode Map

Index of all lode files.

```
lode/
├── summary.md           # project-wide living snapshot
├── terminology.md       # domain language definitions
├── practices.md         # patterns, style, testing, CI practices
├── lode-map.md          # this file
├── core/
│   ├── summary.md       # core API & architecture details
│   └── config.md        # config design: ErgoConfig, env vars, add_output()
├── external/
│   └── evlog.md         # evlog architecture analysis (TypeScript wide-event logging)
├── plans/               # roadmaps & TODOs (currently empty)
└── tmp/                 # git-ignored session scraps
```

## Related files outside lode/
- `src/ergolog/ergolog.py` — entire implementation (single-file library)
- `src/ergolog/__init__.py` — re-exports `eg`, `ErgoConfig`, `ErgoCounter`, `ErgoEvent`, `ErgoFormatter`, `ErgoJSONFormatter`
- `test/test_basic.py` — core feature tests
- `test/test_threading.py` — thread-safety tests (contextvars)
- `test/test_exceptions.py` — exception cleanup tests
- `test/test_counter.py` — ErgoCounter tests
- `test/test_event.py` — ErgoEvent wide event tests
- `test/test_composition.py` — composability tests (counters/timers in tags & events, timer laps)
- `test/test_config.py` — ErgoConfig API tests (add_output, remove_output, set_format, set_level, set_propagate, auto_setup)
- `test/conftest.py` — shared fixture to restore ergolog state between tests