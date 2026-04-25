"""Tests for composability: timer laps, timer/counter as tag/event values, events with counters/timers."""

import logging
from time import sleep
from pytest import LogCaptureFixture

from ergolog import eg
from ergolog.ergolog import ErgoCounter, ErgoTimer


# ---------------------------------------------------------------------------
# Timer .lap()
# ---------------------------------------------------------------------------


def test_timer_lap_returns_float():
    """lap() returns current elapsed time as a float, timer keeps running."""
    with eg.timer() as t:
        sleep(0.05)
        lap1 = t.lap()
        sleep(0.05)
        lap2 = t.lap()

        assert isinstance(lap1, float)
        assert isinstance(lap2, float)
        assert lap2 > lap1
        assert lap1 >= 0.04  # Allow some timing slack


def test_timer_lap_named():
    """lap('name') records a named lap and returns the float."""
    with eg.timer() as t:
        sleep(0.05)
        fetch_lap = t.lap('fetch')
        sleep(0.05)
        process_lap = t.lap('process')

        assert isinstance(fetch_lap, float)
        assert isinstance(process_lap, float)
        assert process_lap > fetch_lap
        assert 'fetch' in t.laps
        assert 'process' in t.laps
        assert t.laps['fetch'] == fetch_lap
        assert t.laps['process'] == process_lap


def test_timer_lap_without_name():
    """lap() without a name does not record in laps dict."""
    with eg.timer() as t:
        sleep(0.01)
        elapsed = t.lap()

        assert isinstance(elapsed, float)
        assert len(t.laps) == 0  # No named laps


def test_timer_laps_property():
    """laps property returns a copy of named laps."""
    with eg.timer() as t:
        t.lap('a')
        t.lap('b')

        laps = t.laps
        assert 'a' in laps
        assert 'b' in laps

        # It's a copy — mutating it doesn't affect the timer
        laps['c'] = 999
        assert 'c' not in t.laps


def test_timer_elapsed_property():
    """elapsed property returns current elapsed time."""
    with eg.timer() as t:
        sleep(0.05)
        e1 = t.elapsed
        sleep(0.05)
        e2 = t.elapsed

        assert isinstance(e1, float)
        assert isinstance(e2, float)
        assert e2 > e1


def test_timer_repr_and_str():
    """__repr__ and __str__ return formatted elapsed time."""
    with eg.timer() as t:
        sleep(0.05)
        r = repr(t)
        s = str(t)

        assert isinstance(r, str)
        assert isinstance(s, str)
        # Should be something like '0.050'
        assert float(r) >= 0.04
        assert float(s) >= 0.04


def test_timer_float_conversion():
    """__float__ returns current elapsed time."""
    with eg.timer() as t:
        sleep(0.05)
        f = float(t)

        assert isinstance(f, float)
        assert f >= 0.04


def test_timer_lap_resets_on_reenter():
    """Named laps should reset when a timer context is re-entered."""
    t = eg.timer()
    with t:
        t.lap('first_pass')
        sleep(0.02)

    # Re-entering the timer should reset laps
    with t:
        assert len(t.laps) == 0


# ---------------------------------------------------------------------------
# Timer as tag value
# ---------------------------------------------------------------------------


def test_timer_as_tag_value(caplog: LogCaptureFixture):
    """Timer as a keyword tag value shows dynamic elapsed per log line."""
    t = eg.timer()
    with eg.tag(elapsed=t):
        sleep(0.05)
        eg.info('step 1')
        sleep(0.05)
        eg.info('step 2')

    assert len(caplog.records) == 2
    # Tag should contain 'elapsed=' and end with 's'
    tag1 = caplog.records[0].tag_list[0]  # type: ignore
    tag2 = caplog.records[1].tag_list[0]  # type: ignore

    assert tag1.startswith('elapsed=')
    assert tag1.endswith('s')
    assert tag2.startswith('elapsed=')
    assert tag2.endswith('s')

    # The elapsed value in tag2 should be larger than tag1
    val1 = float(tag1.split('=')[1].rstrip('s'))
    val2 = float(tag2.split('=')[1].rstrip('s'))
    assert val2 > val1


def test_timer_as_tag_with_counter(caplog: LogCaptureFixture):
    """Timer and counter can both be used as tag values simultaneously."""
    t = eg.timer()
    counter = eg.counter()
    with eg.tag(elapsed=t, step=counter):
        counter += 1
        eg.info('step 1')
        counter += 1
        eg.info('step 2')

    assert len(caplog.records) == 2
    tags1 = caplog.records[0].tag_list  # type: ignore
    tags2 = caplog.records[1].tag_list  # type: ignore

    assert 'step=1' in tags1
    assert 'step=2' in tags2
    # Both records should have elapsed tags
    assert any(t.startswith('elapsed=') for t in tags1)
    assert any(t.startswith('elapsed=') for t in tags2)


# ---------------------------------------------------------------------------
# Counter as event value
# ---------------------------------------------------------------------------


def test_counter_as_event_value():
    """Counter passed to e.set() evaluates at emit time, showing current value."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        counter = eg.counter()
        with eg.event(op='batch') as e:
            e.set(processed=counter)
            counter += 5
            counter += 3

        assert len(messages) == 1
        record = messages[0]
        # Counter should show its final value (8), not the value when set() was called
        assert record.event['processed'] == 8
    finally:
        eg._logger.removeHandler(handler)


def test_counter_as_event_value_with_initial_zero():
    """Counter in event shows 0 if no increments before emit."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        counter = eg.counter()
        e = eg.event(op='idle')
        e.set(count=counter)
        e.emit()

        assert len(messages) == 1
        assert messages[0].event['count'] == 0
    finally:
        eg._logger.removeHandler(handler)


# ---------------------------------------------------------------------------
# Timer as event value
# ---------------------------------------------------------------------------


def test_timer_as_event_value():
    """Timer passed to e.set() evaluates elapsed at emit time."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        t = eg.timer()
        with eg.event(op='timed') as e:
            e.set(duration=t)
            sleep(0.05)

        assert len(messages) == 1
        record = messages[0]
        # Timer should show total elapsed time, not the time when set() was called
        assert record.event['duration'] >= 0.04
    finally:
        eg._logger.removeHandler(handler)


# ---------------------------------------------------------------------------
# Named laps auto-collected in events
# ---------------------------------------------------------------------------


def test_timer_named_laps_in_event():
    """Named laps on a timer are auto-collected into event context."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        t = eg.timer()
        with eg.event(op='pipeline') as e:
            e.set(duration=t)
            sleep(0.02)
            t.lap('fetch')
            sleep(0.02)
            t.lap('process')

        assert len(messages) == 1
        record = messages[0]
        # Event should include named laps
        assert 'fetch' in record.event
        assert 'process' in record.event
        assert record.event['fetch'] >= 0.01
        assert record.event['process'] > record.event['fetch']
        # Timer duration should also be present
        assert 'duration' in record.event
    finally:
        eg._logger.removeHandler(handler)


def test_timer_laps_without_timer_in_event():
    """Named laps on a timer that wasn't set into the event still get collected if timer was set separately later."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        t = eg.timer()
        e = eg.event(op='task')
        t.lap('startup')
        e.set(duration=t)
        t.lap('complete')
        e.emit()

        assert len(messages) == 1
        record = messages[0]
        assert 'startup' in record.event
        assert 'complete' in record.event
    finally:
        eg._logger.removeHandler(handler)


def test_explicit_lap_set_in_event():
    """Using e.set(fetch=t.lap()) — explicit control over event context."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        with eg.event(op='task') as e:
            t = eg.timer()
            sleep(0.02)
            e.set(fetch_time=t.lap())  # Explicitly set lap value
            sleep(0.02)
            e.set(process_time=t.lap())  # Explicitly set lap value

        assert len(messages) == 1
        record = messages[0]
        assert 'fetch_time' in record.event
        assert 'process_time' in record.event
        assert record.event['process_time'] > record.event['fetch_time']
        # Since we used t.lap() (unnamed), no auto-collected laps
        # But we also didn't set duration=t, so no timer reference in context
    finally:
        eg._logger.removeHandler(handler)


# ---------------------------------------------------------------------------
# Combined: counter + timer + event
# ---------------------------------------------------------------------------


def test_event_with_counter_and_timer():
    """Event with both counter and timer evaluates both at emit time."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        counter = eg.counter()
        t = eg.timer()
        with eg.event(op='combined') as e:
            e.set(count=counter, duration=t)
            for i in range(3):
                counter += 1
                t.lap(f'step_{counter._value}')

        assert len(messages) == 1
        record = messages[0]
        assert record.event['count'] == 3
        assert record.event['duration'] >= 0.0
        assert 'step_1' in record.event
        assert 'step_2' in record.event
        assert 'step_3' in record.event
    finally:
        eg._logger.removeHandler(handler)


def test_event_warn():
    """e.warn() sets level to WARNING and optionally records a message."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        e = eg.event(op='degraded')
        e.warn('fallback used')
        e.emit()

        assert len(messages) == 1
        record = messages[0]
        assert record.levelname == 'WARNING'
        assert record.event['warning'] == 'fallback used'
    finally:
        eg._logger.removeHandler(handler)


def test_event_warn_with_context():
    """e.warn() can include additional context."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        e = eg.event(op='payment')
        e.warn('retry', attempts=3)
        e.emit()

        assert len(messages) == 1
        record = messages[0]
        assert record.levelname == 'WARNING'
        assert record.event['warning'] == 'retry'
        assert record.event['attempts'] == 3
    finally:
        eg._logger.removeHandler(handler)


def test_event_warn_no_message():
    """e.warn() without a message just sets the level."""
    messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)

    handler = CaptureHandler()
    eg._logger.addHandler(handler)

    try:
        e = eg.event(op='minor')
        e.warn()
        e.emit()

        assert len(messages) == 1
        record = messages[0]
        assert record.levelname == 'WARNING'
        assert 'warning' not in record.event
    finally:
        eg._logger.removeHandler(handler)