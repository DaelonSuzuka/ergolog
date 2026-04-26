# Practices

## Code Style
- **Formatter**: ruff (line-length 120, single quotes)
- **Python version**: >=3.9
- **Type hints**: modern PEP 604 union (`str | None`) with `from __future__ import annotations`; lowercase generics (`list[str]`, `dict[str, Any]`) via PEP 585
- **No runtime dependencies** — ergolog is zero-dependency
- **Dev dependencies**: pytest>=8.4.1, pytest-cov>=6.2.1

## Self-test / Demo Reel
- `src/ergolog/ergolog.py` has an `if __name__ == '__main__'` block at the bottom
- Serves as a smoke test, demo reel, and internal example — exercises all major features
- Not exhaustive, but must hit the main points and stay up-to-date with the current API
- Run with: `uv run python src/ergolog/ergolog.py`

## Architecture Patterns
- **Singleton entry point**: `eg = ErgoLog()` is the single exported instance
- **Logger caching**: `ErgoLog._loggers` dict caches all named loggers by fully-qualified name
- **Context-local tag state**: `ErgoTagger._tag_stack_var` is a `contextvars.ContextVar`; each thread and async task gets its own isolated tag stack via `set()/reset(token)`
- **Logger delegation**: `ErgoLog` wraps a stdlib `logging.Logger` stored as `self._logger`; standard log methods are bound directly to avoid `__getattr__` overhead
- **Auto-setup on import**: if `ERGOLOG_NO_AUTO_SETUP` is not set and the logger has no handlers, `ErgoConfig` adds a stdout handler with `ErgoFormatter`
- **Color as opt-in/opt-out**: colors enabled by default; `ERGOLOG_NO_COLORS` strips all ANSI codes

## Testing
- Tests use `pytest` with `LogCaptureFixture` (caplog) to inspect `LogRecord` objects
- Tag assertions check `record.tags` (a custom attribute injected by `ErgoFormatter`)
- Timer tests tolerate timing variance (e.g. `'took 0.10' in message`)
- Exception cleanup tests in `test/test_exceptions.py` verify that tags, timers, and trace all clean up correctly when exceptions propagate through them
- Threading tests in `test/test_threading.py` verify context isolation via `contextvars` — barriers force threads into concurrent tag contexts

## Build & CI
- Package manager: `uv`
- CI: GitHub Actions (`ci.yml`) on push to `master`, matrix: Python 3.9–3.12
- Install: `uv sync --locked --all-extras --dev`
- Test: `uv run pytest`