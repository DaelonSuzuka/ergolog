# Lode Map

Index of all lode files.

```
lode/
├── summary.md           # project-wide living snapshot
├── terminology.md       # domain language definitions
├── practices.md         # patterns, style, testing, CI practices
├── lode-map.md          # this file
├── core/
│   └── summary.md       # core API & architecture details
├── external/
│   └── evlog.md         # evlog architecture analysis (TypeScript wide-event logging)
├── plans/               # roadmaps & TODOs (currently empty)
└── tmp/                 # git-ignored session scraps
```

## Related files outside lode/
- `src/ergolog/ergolog.py` — entire implementation (single-file library)
- `src/ergolog/__init__.py` — re-exports `eg`, `config`, `ErgoCounter`
- `test/test_basic.py` — core feature tests
- `test/test_threading.py` — thread-safety tests (contextvars)
- `test/test_exceptions.py` — exception cleanup tests
- `test/test_counter.py` — ErgoCounter tests
- `test/test_event.py` — ErgoEvent wide event tests
- `test/test_composition.py` — composability tests (counters/timers in tags & events, timer laps)
- `test/main.py` — manual/demo script
- `.github/workflows/ci.yml` — CI (Python 3.9–3.13)
- `pyproject.toml` — project metadata, ruff config, dev deps