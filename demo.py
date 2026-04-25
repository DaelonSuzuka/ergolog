"""ergolog demo — each section is a function decorated with @demo.

Run with: uv run python demo.py
"""

import inspect
import tokenize
import io
import keyword

from time import sleep
from ergolog import eg


# ── ANSI syntax highlighting via tokenize ──────────────────────────────────────

STYLES = {
    tokenize.NAME:       '\033[33m',   # yellow — identifiers
    tokenize.OP:         '\033[37m',   # white — operators/punctuation
    tokenize.NUMBER:      '\033[36m',   # cyan — numbers
    tokenize.STRING:      '\033[32m',   # green — strings
    tokenize.COMMENT:     '\033[2m',    # dim — comments
}

# 3.12+ added f-string token types — add them if available
for _ft in ('FSTRING', 'FSTRING_START', 'FSTRING_END', 'FSTRING_MIDDLE'):
    if hasattr(tokenize, _ft):
        STYLES[getattr(tokenize, _ft)] = '\033[32m'
KEYWORD_STYLE = '\033[35m'              # magenta — Python keywords
BUILTIN_STYLE = '\033[33m'             # yellow — builtins (same as NAME)
RESET = '\033[0m'
BUILTIN_NAMES = set(__builtins__) if isinstance(__builtins__, dict) else set(dir(__builtins__))

_demorange = '\033[36m'  # cyan for the >>> prompt


def highlight(source: str) -> str:
    """Add ANSI color codes to Python source using the tokenize module."""
    lines = source.splitlines(keepends=True)
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        # Fallback: no highlighting if tokenize fails
        return source

    # Build a map of (line, col) -> style for each token
    highlights = {}
    for tok in tokens:
        tok_type, tok_string, start, end, _ = tok
        start_line, start_col = start
        end_line, end_col = end

        if tok_type == tokenize.NAME and keyword.iskeyword(tok_string):
            style = KEYWORD_STYLE
        elif tok_type in STYLES:
            style = STYLES[tok_type]
        elif tok_type == tokenize.ENDMARKER:
            continue
        else:
            style = None

        if style:
            highlights.setdefault(start_line - 1, []).append((start_col, end_col if end_line == start_line else len(lines[start_line - 1]), style))

    # Apply highlights per line
    result_lines = []
    for i, line in enumerate(lines):
        if i not in highlights:
            result_lines.append(line)
            continue
        # Sort highlights by column, rightmost first to preserve positions
        parts = []
        col_ranges = sorted(highlights[i], key=lambda x: x[0])
        pos = 0
        for start_col, end_col, style in col_ranges:
            if start_col > pos:
                parts.append(line[pos:start_col])
            parts.append(style)
            parts.append(line[start_col:end_col])
            parts.append(RESET)
            pos = end_col
        if pos < len(line):
            parts.append(line[pos:])
        result_lines.append(''.join(parts))

    return ''.join(result_lines)


def get_body(func):
    """Extract the function body, dedented, skipping decorator and def lines."""
    lines = inspect.getsource(func).splitlines()
    # Skip decorator lines (@demo) and the def line
    start = 0
    while lines[start].strip().startswith('@'):
        start += 1
    # Skip the def line itself
    start += 1
    # Skip blank lines after def
    while start < len(lines) and lines[start].strip() == '':
        start += 1
    body_lines = lines[start:]
    import textwrap
    return textwrap.dedent('\n'.join(body_lines))


# ── Demo registry ────────────────────────────────────────────────────────────

_demos = []


def demo(func):
    """Register a demo function. Its body is printed then executed."""
    _demos.append((func.__name__, func))
    return func


def run_demos():
    """Run all registered demos, printing syntax-highlighted code first."""
    for name, func in _demos:
        title = name.replace('_', ' ').title()
        print(f'\n{"=" * 80}')
        print(f'  {title}')
        print(f'{"=" * 80}\n')

        body = get_body(func)
        highlighted = highlight(body)

        for line in highlighted.splitlines():
            print(f'  {STYLES.get(tokenize.OP, "")}>>>{RESET} {line}')
        print()
        func()

    print(f'\n{"=" * 80}')
    print('  Demo complete!')
    print(f'{"=" * 80}\n')


# ── Demo functions ────────────────────────────────────────────────────────────

@demo
def basic_usage():
    eg.debug('debug')
    eg.info('info')
    eg.warning('warning')
    eg.error('error')
    eg.critical('critical')


@demo
def named_loggers():
    log = eg('test')
    log.info('named logger')


@demo
def child_loggers():
    one = eg('one')
    two = one('two')
    two.info('child logger')


@demo
def tags():
    with eg.tag('tag1'):
        eg.info('one tag')
        with eg.tag('tag2'):
            eg.info('two tags')
        eg.info('one tag again')


@demo
def keyword_tags():
    with eg.tag(keyword='tags', comma='multiple'):
        eg.debug('')
        with eg.tag('regular tag'):
            eg.info('')
            with eg.tag(more='keywords'):
                eg.info('')
        eg.debug('')


@demo
def auto_generated_ids():
    with eg.tag(job=eg.uid):
        eg.info('first')
        with eg.tag(job=eg.uid):
            eg.info('nested')
        eg.info('first again')


@demo
def counters():
    counter = eg.counter()
    with eg.tag(step=counter):
        eg.info('start')       # step=0
        counter += 1
        eg.info('middle')      # step=1
        counter += 1
        eg.info('end')         # step=2


@demo
def counter_loop_enumeration():
    loops = eg.counter()
    with eg.tag(i=loops):
        for item in loops.count(['a', 'b', 'c']):
            eg.info(f'item {item}')


@demo
def counter_accumulation():
    total = eg.counter()
    with eg.tag(bytes=total):
        total += 1024
        eg.info('chunk')       # bytes=1024
        total += 512
        eg.info('chunk')       # bytes=1536


@demo
def timer_with_callback():
    with eg.timer(lambda t: eg.debug(f'took {t}S')):
        eg.info('before')
        sleep(0.05)
        eg.info('after')


@demo
def timer_as_context_manager():
    with eg.timer() as t:
        eg.info('before')
        sleep(0.05)
        eg.info('after')

    eg.debug(f'took {t} S')


@demo
def timer_laps():
    with eg.timer() as t:
        sleep(0.02)
        fetch_time = t.lap()
        sleep(0.02)
        process_time = t.lap()
        eg.debug(f'fetch={fetch_time:.3f}s process={process_time:.3f}s total={t.elapsed:.3f}s')


@demo
def timer_named_laps():
    with eg.timer() as t:
        sleep(0.02)
        t.lap('fetch')
        sleep(0.02)
        t.lap('process')

    eg.info(f'laps: {t.laps}')


@demo
def timer_as_tag_value():
    t = eg.timer()
    with eg.tag(elapsed=t):
        eg.info('start')
        sleep(0.05)
        eg.info('middle')
        sleep(0.05)
        eg.info('end')


@demo
def timer_and_counter_as_tags():
    t = eg.timer()
    counter = eg.counter()
    with eg.tag(elapsed=t, step=counter):
        eg.info('step 1')
        counter += 1
        sleep(0.05)
        eg.info('step 2')
        counter += 1
        eg.info('step 3')


@demo
def trace_decorator():
    @eg.trace()
    def my_function(a, b):
        return a + b

    my_function(2, 2)


@demo
def wide_event_context_manager():
    with eg.event(user='alice', action='checkout') as e:
        e.set(cart={'items': 3, 'total': 9999})
        e.set(payment={'method': 'card'})


@demo
def wide_event_manual_emit():
    e = eg.event(user='bob', action='search')
    e.set(query='ergonomics', results=42)
    e.emit()


@demo
def event_with_warning():
    with eg.event(user='alice', action='payment') as e:
        e.warn('used fallback method', attempts=3)


@demo
def event_with_error():
    try:
        with eg.event(user='charlie', action='failing_op') as e:
            e.set(step='processing')
            raise ValueError('insufficient funds')
    except ValueError:
        pass


@demo
def event_capturing_tags():
    with eg.tag(request_id='abc123'):
        with eg.event(operation='tagged_op') as e:
            e.set(extra='data')


@demo
def counter_as_event_value():
    counter = eg.counter()
    with eg.event(op='batch') as e:
        e.set(processed=counter)
        for i in range(3):
            counter += 1


@demo
def timer_as_event_value():
    with eg.event(op='export') as e:
        t = eg.timer()
        e.set(duration=t)
        sleep(0.05)


@demo
def named_laps_in_events():
    t = eg.timer()
    with eg.event(op='pipeline') as e:
        e.set(duration=t)
        sleep(0.02)
        t.lap('fetch')
        sleep(0.02)
        t.lap('process')
        sleep(0.02)
        t.lap('save')


@demo
def explicit_lap_values_in_events():
    with eg.event(op='task') as e:
        t = eg.timer()
        sleep(0.02)
        e.set(fetch_time=t.lap())
        sleep(0.02)
        e.set(process_time=t.lap())


@demo
def counter_timer_event_together():
    counter = eg.counter()
    t = eg.timer()
    with eg.event(op='process_batch') as e:
        e.set(duration=t, items=counter)
        for i in range(3):
            sleep(0.01)
            counter += 1
            t.lap(f'item_{i + 1}')


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    run_demos()