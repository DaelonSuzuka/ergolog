from time import sleep
from pytest import LogCaptureFixture

from ergolog import eg


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


def test_trace(caplog: LogCaptureFixture):
    @eg.trace
    def trace_me(a, b):
        return a + b

    trace_me(2, 2)

    assert len(caplog.records) == 3

    assert caplog.records[0].message == 'registering trace'
    assert caplog.records[0].levelname == 'DEBUG'

    assert caplog.records[1].message == 'executing (2, 2) {}'
    assert caplog.records[1].levelname == 'DEBUG'

    assert 'done in 0.000' in caplog.records[2].message
    assert 'S returned: 4' in caplog.records[2].message
    assert caplog.records[2].levelname == 'DEBUG'
