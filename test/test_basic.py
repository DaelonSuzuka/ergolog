import pytest

from ergolog import eg


def test_basic_logging():
    eg.debug('debug')
    eg.info('info')
    eg.warning('warning')
    eg.error('error')
    eg.critical('critical')


def test_named_loggers():
    log = eg('named_logger')
    log.debug('debug')
    log.info('info')
    log.warning('warning')
    log.error('error')
    log.critical('critical')


def test_child_loggers():
    eg.info('')
    one = eg('one')
    one.info('')

    two = one('two')
    two.info('')
