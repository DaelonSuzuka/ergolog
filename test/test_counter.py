"""Tests for ErgoCounter — counter/accumulator tag values."""

from pytest import LogCaptureFixture

from ergolog import eg


def test_counter_starts_at_zero(caplog: LogCaptureFixture):
    counter = eg.counter()
    with eg.tag(step=counter):
        eg.info('first')  # step=0

    assert len(caplog.records) == 1
    assert caplog.records[0].tags == '[step=0] '  # type: ignore
    assert caplog.records[0].tag_list == ['step=0']  # type: ignore


def test_counter_increments(caplog: LogCaptureFixture):
    counter = eg.counter()
    with eg.tag(step=counter):
        eg.info('before')      # step=0
        counter += 1
        eg.info('after')       # step=1

    assert len(caplog.records) == 2
    assert caplog.records[0].tags == '[step=0] '  # type: ignore
    assert caplog.records[1].tags == '[step=1] '  # type: ignore


def test_counter_accumulates(caplog: LogCaptureFixture):
    total = eg.counter()
    with eg.tag(bytes=total):
        total += 1024
        eg.info('read')        # bytes=1024
        total += 512
        eg.info('read')        # bytes=1536

    assert len(caplog.records) == 2
    assert caplog.records[0].tags == '[bytes=1024] '  # type: ignore
    assert caplog.records[1].tags == '[bytes=1536] '  # type: ignore


def test_counter_count_loop(caplog: LogCaptureFixture):
    counter = eg.counter()
    with eg.tag(i=counter):
        for _ in counter.count(range(5)):
            eg.info('step')

    assert len(caplog.records) == 5
    for i, record in enumerate(caplog.records, start=1):
        assert record.tags == f'[i={i}] '  # type: ignore


def test_counter_named_count_loop(caplog: LogCaptureFixture):
    counter = eg.counter()
    with eg.tag(request=counter):
        for url in counter.count(['a', 'b', 'c']):
            eg.info(f'fetching {url}')

    assert len(caplog.records) == 3
    assert caplog.records[0].tags == '[request=1] '  # type: ignore
    assert caplog.records[1].tags == '[request=2] '  # type: ignore
    assert caplog.records[2].tags == '[request=3] '  # type: ignore


def test_counter_mixed_with_tags(caplog: LogCaptureFixture):
    counter = eg.counter()
    with eg.tag(job=eg.uid, step=counter):
        counter += 1
        eg.info('processing')
        counter += 1
        eg.info('done')

    assert len(caplog.records) == 2
    assert 'job=' in caplog.records[0].tags  # type: ignore
    assert 'step=1' in caplog.records[0].tags  # type: ignore
    assert 'step=2' in caplog.records[1].tags  # type: ignore


def test_counter_subtraction(caplog: LogCaptureFixture):
    counter = eg.counter()
    with eg.tag(remaining=counter):
        counter += 10
        eg.info('got batch')       # remaining=10
        counter -= 3
        eg.info('processed some')  # remaining=7

    assert len(caplog.records) == 2
    assert caplog.records[0].tags == '[remaining=10] '  # type: ignore
    assert caplog.records[1].tags == '[remaining=7] '  # type: ignore


def test_counter_equality():
    counter = eg.counter()
    assert counter == 0
    counter += 5
    assert counter == 5
    assert counter != 3


def test_counter_repr_and_str():
    counter = eg.counter()
    assert repr(counter) == '0'
    assert str(counter) == '0'
    counter += 42
    assert repr(counter) == '42'
    assert str(counter) == '42'