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
    
    assert caplog.records[0].tags == '[a] '
    assert caplog.records[1].tags == '[a, b] '
    assert caplog.records[2].tags == '[a] '
    
    
def test_kwtags(caplog: LogCaptureFixture):
    with eg.tag(keyword='tags', comma='multiple'):
        eg.debug('')
        with eg.tag('regular_tag'):
            eg.info('')
            with eg.tag(more='keywords'):
                eg.info('')
        eg.debug('')