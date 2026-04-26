from time import sleep
from pytest import LogCaptureFixture

from ergolog import eg, ErgoConfig


def test_config_exposed():
    assert isinstance(eg.config, ErgoConfig)
    assert hasattr(eg.config, 'add_output')
    assert hasattr(eg.config, 'remove_output')
    assert hasattr(eg.config, 'set_format')


def test_basic_logging(caplog: LogCaptureFixture):
    eg.debug('debug')
    eg.info('info')
    eg.warning('warning')
    eg.error('error')
    eg.critical('critical')

    assert len(caplog.records) == 5

    assert caplog.records[0].name == 'ergo'

    assert caplog.records[0].message == 'debug'
    assert caplog.records[1].message == 'info'
    assert caplog.records[2].message == 'warning'
    assert caplog.records[3].message == 'error'
    assert caplog.records[4].message == 'critical'


def test_named_loggers(caplog: LogCaptureFixture):
    log = eg('named_logger')
    log.debug('debug')

    assert len(caplog.records) == 1

    assert caplog.records[0].name == 'ergo.named_logger'
    assert caplog.records[0].message == 'debug'

    same = eg()

    assert same._logger is eg._logger
    other = eg('other')
    other2 = eg('other')

    assert other._logger is other2._logger
    assert other is other2


def test_child_loggers(caplog: LogCaptureFixture):
    eg.info('')
    one = eg('one')
    one.info('')

    two = one('two')
    two.info('')

    assert len(caplog.records) == 3

    assert caplog.records[0].name == 'ergo'
    assert caplog.records[1].name == 'ergo.one'
    assert caplog.records[2].name == 'ergo.one.two'


def test_named_logger_edge_cases():
    """Document identity and caching behavior for named logger edge cases."""
    # Empty string returns root identity
    root = eg('')
    assert root is eg
    assert root._name == 'ergo'

    # Fully qualified root name returns identity
    root2 = eg('ergo')
    assert root2 is eg

    # Trailing dot absorbed, returns identity
    root3 = eg('ergo.')
    assert root3 is eg

    # From a child, empty string returns identity
    one = eg('one')
    same_one = one('')
    assert same_one is one

    # From a child, fully qualified self-name returns identity
    same_one2 = one('ergo.one')
    assert same_one2 is one

    # Redundant prefix is stripped when creating grandchildren
    two = one('ergo.one.two')
    assert two._name == 'ergo.one.two'
    two2 = one('two')
    assert two2 is two

    # Caching: multiple lookups return same instance
    three = eg('three')
    three_again = eg('three')
    assert three is three_again



def test_tags(caplog: LogCaptureFixture):
    with eg.tag('a'):
        eg.info('one tag')
        with eg.tag('b'):
            eg.info('two tags')
        eg.info('one tag')

    assert len(caplog.records) == 3

    assert caplog.records[0].tags == '[a] '  # type: ignore
    assert caplog.records[1].tags == '[a, b] '  # type: ignore
    assert caplog.records[2].tags == '[a] '  # type: ignore


def test_tag_list_structured(caplog: LogCaptureFixture):
    with eg.tag('positional', keyword='val'):
        eg.info('test')
        with eg.tag('inner'):
            eg.info('nested')

    assert len(caplog.records) == 2

    assert caplog.records[0].tag_list == ['positional', 'keyword=val']  # type: ignore
    assert caplog.records[1].tag_list == ['positional', 'keyword=val', 'inner']  # type: ignore

    # no tags outside context
    eg.info('no tags')
    assert caplog.records[2].tag_list == []  # type: ignore


def test_kwtags(caplog: LogCaptureFixture):
    with eg.tag(a='a'):
        eg.debug('')
        with eg.tag('tag'):
            eg.info('')
            with eg.tag(b='b'):
                eg.info('')
        eg.debug('')

    assert len(caplog.records) == 4

    assert caplog.records[0].tags == '[a=a] '  # type: ignore
    assert caplog.records[1].tags == '[a=a, tag] '  # type: ignore
    assert caplog.records[2].tags == '[a=a, tag, b=b] '  # type: ignore
    assert caplog.records[3].tags == '[a=a] '  # type: ignore


def test_tag_decorator(caplog: LogCaptureFixture):
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

    assert len(caplog.records) == 5

    assert caplog.records[0].tags == ''  # type: ignore
    assert caplog.records[0].message == 'start'
    assert caplog.records[1].tags == '[outer] '  # type: ignore
    assert caplog.records[1].message == 'before'
    assert caplog.records[2].tags == '[outer, inner] '  # type: ignore
    assert caplog.records[2].message == 'test'
    assert caplog.records[3].tags == '[outer] '  # type: ignore
    assert caplog.records[3].message == 'after'
    assert caplog.records[4].tags == ''  # type: ignore
    assert caplog.records[4].message == 'end'


def test_timer(caplog: LogCaptureFixture):
    with eg.timer(lambda t: eg.debug(f'took {t}S')):
        eg.info('before')
        sleep(0.1)
        eg.info('after')

    assert len(caplog.records) == 3

    assert caplog.records[0].message == 'before'
    assert caplog.records[1].message == 'after'
    assert 'took 0.10' in caplog.records[2].message


def test_timer_decorator(caplog: LogCaptureFixture):
    @eg.timer(lambda t: eg.debug(f'took {t}S'))
    def time_me():
        sleep(0.1)
        eg.info('inside')

    time_me()

    assert len(caplog.records) == 2

    assert caplog.records[0].message == 'inside'
    assert 'took 0.10' in caplog.records[1].message


def test_timer_no_callback(caplog: LogCaptureFixture):
    """Timer with no callback should work as a context manager with repr."""
    with eg.timer() as t:
        sleep(0.05)

    elapsed = float(repr(t))
    assert elapsed >= 0.04

    # No timer log should appear — callback is None
    timer_logs = [r for r in caplog.records if 'took' in r.message]
    assert len(timer_logs) == 0


def test_trace(caplog: LogCaptureFixture):
    @eg.trace()
    def trace_me(a, b):
        return a + b

    trace_me(2, 2)

    assert len(caplog.records) == 2

    assert caplog.records[0].message == 'registering trace'
    assert caplog.records[0].levelname == 'WARNING'

    # default: no args or return value logged
    assert 'done in 0.000' in caplog.records[1].message
    assert 'S returned:' not in caplog.records[1].message
    assert caplog.records[1].levelname == 'DEBUG'


def test_trace_log_args(caplog: LogCaptureFixture):
    @eg.trace(log_args=True)
    def trace_me(a, b):
        return a + b

    trace_me(2, 2)

    assert len(caplog.records) == 3

    assert caplog.records[0].message == 'registering trace'
    assert caplog.records[0].levelname == 'WARNING'

    assert caplog.records[1].message == 'executing (2, 2) {}'
    assert caplog.records[1].levelname == 'DEBUG'

    assert 'done in 0.000' in caplog.records[2].message
    assert 'S returned: 4' in caplog.records[2].message
    assert caplog.records[2].levelname == 'DEBUG'


def test_callable_tags(caplog: LogCaptureFixture):
    counter = iter(range(100))

    with eg.tag(request_id=lambda: f'req-{next(counter)}'):
        eg.info('first')
        with eg.tag(request_id=lambda: f'req-{next(counter)}'):
            eg.info('nested')

    assert len(caplog.records) == 2

    # Outer tag is req-0, nested adds req-1 on top
    assert caplog.records[0].tags == '[request_id=req-0] '  # type: ignore
    assert caplog.records[1].tags == '[request_id=req-0, request_id=req-1] '  # type: ignore


def test_uid_helper(caplog: LogCaptureFixture):
    with eg.tag(job=eg.uid):
        eg.info('one')
        with eg.tag(job=eg.uid):
            eg.info('two')

    assert len(caplog.records) == 2

    # Each entry generates a unique 6-char hex ID
    outer = caplog.records[0].tag_list[0]  # type: ignore
    inner = caplog.records[1].tag_list[1]  # type: ignore  — nested, so second tag

    assert outer.startswith('job=')
    assert inner.startswith('job=')
    assert len(outer) == 10  # 'job=' + 6 chars
    assert len(inner) == 10
    assert outer != inner  # unique per entry
