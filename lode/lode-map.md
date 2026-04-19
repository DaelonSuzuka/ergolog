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
├── plans/               # roadmaps & TODOs (currently empty)
└── tmp/                 # git-ignored session scraps
```

## Related files outside lode/
- `src/ergolog/ergolog.py` — entire implementation (single-file library)
- `src/ergolog/__init__.py` — re-exports `eg`
- `test/test_basic.py` — all tests
- `test/main.py` — manual/demo script
- `pyproject.toml` — project metadata, ruff config, dev deps