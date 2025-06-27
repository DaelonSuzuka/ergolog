[![.github/workflows/ci.yml](https://github.com/DaelonSuzuka/ergolog/actions/workflows/ci.yml/badge.svg)](https://github.com/DaelonSuzuka/ergolog/actions/workflows/ci.yml)

# ergolog
A minimal, ergonomic python logging wrapper

## Intallation

```shell
uv add ergolog
# or
pip install ergolog
```

## Basic Usage


```py
from ergolog import eg

eg.debug('debug')
eg.info('info')
eg.warning('warning')
eg.error('error')
eg.critical('critical')
```

```
[DEBUG   ] ergo (main.py:3) debug
[INFO    ] ergo (main.py:4) info
[WARNING ] ergo (main.py:5) warning
[ERROR   ] ergo (main.py:6) error
[CRITICAL] ergo (main.py:7) critical
```

## Advanced Usage

Named loggers

```py
from ergolog import eg

eg('test').debug('named logger')

```

```
[DEBUG   ] ergo.test (main.py:3) named logger
```

Tags


```py
from ergolog import eg

with eg.tag('tag1'):
    eg.info('one tag')
    with eg.tag('tag2'):
        eg.info('two tags')
    eg.info('one tag again')
```

```
[INFO    ] ergo [tag1] (main.py:4) one tag
[INFO    ] ergo [tag1, tag2] (main.py:6) two tags
[INFO    ] ergo [tag1] (main.py:7) one tag again
```

Tag Decorator

```py
from ergolog import eg

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
```

```
[DEBUG   ] ergo (main.py:14) start
[DEBUG   ] ergo [outer] (main.py:9) before
[INFO    ] ergo [outer, inner] (main.py:5) test
[DEBUG   ] ergo [outer] (main.py:12) after
```

Kwarg Tags

```py
from ergolog import eg

with eg.tag(keyword='tags', comma='multiple'):
    eg.debug('')
    with eg.tag('regular tag'):
        eg.info('')
        with eg.tag(more='keywords'):
            eg.info('')
    eg.debug('')
```

```
[DEBUG   ] ergo [keyword=tags, comma=multiple] (main.py:4) 
[INFO    ] ergo [keyword=tags, comma=multiple, regular tag] (main.py:6) 
[INFO    ] ergo [keyword=tags, comma=multiple, regular tag, more=keywords] (main.py:8)
[DEBUG   ] ergo [keyword=tags, comma=multiple] (main.py:9)
```

<!-- 
Job IDs

```py
from ergolog import eg

with eg.tag('job'):
    eg.info('')
    with eg.tag('job'):
        eg.info('nested job ID')
    eg.info('')
```

```
[INFO    ] ergo [job=34bfbe] (main.py:4) 
[INFO    ] ergo [job=34bfbe, job=80dbc9] (main.py:6) nested job ID
[INFO    ] ergo [job=34bfbe] (main.py:7)
```
-->
