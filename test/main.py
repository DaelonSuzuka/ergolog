from ergolog import eg


eg.debug('debug')
eg.info('info')
eg.warning('warning')
eg.error('error')
eg.critical('critical')

print('-' * 100)

log = eg('named_logger')
log.debug('debug')
log.info('info')
log.warning('warning')
log.error('error')
log.critical('critical')

print('-' * 100)

with eg.tag('with_tag'):
    eg.info('one tag')
    with eg.tag('and'):
        eg.info('two tags')
        with eg.tag('more_tags'):
            eg.info('three tags')

print('-' * 100)

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

print('-' * 100)

with eg.tag('job'):
    eg.info('nested job ID')
    with eg.tag('job'):
        eg.info('')
    eg.info('')

print('-' * 100)

with eg.tag(keyword='tags', comma='multiple'):
    eg.debug('')
    with eg.tag('regular tag'):
        eg.info('')
        with eg.tag(more='keywords'):
            eg.info('')
    eg.debug('')
