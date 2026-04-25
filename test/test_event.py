"""Tests for ErgoEvent wide event functionality."""
import logging
import pytest
from ergolog.ergolog import eg, ErgoEvent, ErgoJSONFormatter


def test_event_context_manager():
    """Event as context manager auto-emits on exit."""
    messages = []
    
    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        with eg.event(user='alice', action='test') as e:
            e.set(extra='data')
        
        assert len(messages) == 1
        record = messages[0]
        assert record.levelname == 'INFO'
        assert hasattr(record, 'event')
        assert record.event['user'] == 'alice'
        assert record.event['action'] == 'test'
        assert record.event['extra'] == 'data'
        assert 'duration_s' in record.event
    finally:
        eg._logger.removeHandler(handler)


def test_event_manual_emit():
    """Event can be emitted manually."""
    messages = []
    
    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        e = eg.event(user='bob')
        e.set(action='manual')
        e.emit()
        
        assert len(messages) == 1
        record = messages[0]
        assert record.event['user'] == 'bob'
        assert record.event['action'] == 'manual'
    finally:
        eg._logger.removeHandler(handler)


def test_event_sealed_after_emit():
    """After emit(), further set() calls are ignored."""
    messages = []
    
    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        e = eg.event(user='charlie')
        e.emit()
        e.set(ignored='data')  # Should be ignored
        
        assert len(messages) == 1
        assert 'ignored' not in messages[0].event
    finally:
        eg._logger.removeHandler(handler)


def test_event_error_context():
    """e.error() sets level to ERROR and captures error info."""
    messages = []
    
    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        err = ValueError('test error')
        e = eg.event(user='dave')
        e.error(err, step='failed')
        e.emit()
        
        assert len(messages) == 1
        record = messages[0]
        assert record.levelname == 'ERROR'
        assert 'ValueError' in record.getMessage()
    finally:
        eg._logger.removeHandler(handler)


def test_event_exception_in_context():
    """Exceptions in context manager set ERROR level and still emit."""
    messages = []
    
    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        try:
            with eg.event(user='eve') as e:
                e.set(step='processing')
                raise ValueError('boom')
        except ValueError:
            pass  # Suppress for test
        
        assert len(messages) == 1
        record = messages[0]
        assert record.levelname == 'ERROR'
        assert 'ValueError' in record.getMessage()
        assert 'boom' in record.getMessage()
    finally:
        eg._logger.removeHandler(handler)


def test_event_captures_tags():
    """Event captures current tag stack at emit time."""
    messages = []
    
    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        with eg.tag(request_id='abc123'):
            e = eg.event(user='frank')
            e.set(action='tagged')
            e.emit()
        
        assert len(messages) == 1
        record = messages[0]
        assert 'tags' in record.event
        assert record.event['tags']['request_id'] == 'abc123'
    finally:
        eg._logger.removeHandler(handler)


def test_event_duration():
    """Event captures duration."""
    import time
    
    messages = []
    
    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        with eg.event(user='george') as e:
            time.sleep(0.01)  # 10ms
        
        assert len(messages) == 1
        record = messages[0]
        assert hasattr(record, 'duration')
        assert record.duration >= 0.01
    finally:
        eg._logger.removeHandler(handler)


def test_event_context_property():
    """event.context returns a copy of accumulated context."""
    e = eg.event(user='harry')
    e.set(action='test')
    
    ctx = e.context
    assert ctx['user'] == 'harry'
    assert ctx['action'] == 'test'
    
    # Mutating the copy doesn't affect the event
    ctx['mutated'] = True
    assert 'mutated' not in e.context


def test_event_duration_property():
    """event.duration returns elapsed time."""
    import time
    
    e = eg.event(user='ike')
    time.sleep(0.01)
    
    duration = e.duration
    assert duration >= 0.01
    
    # Duration keeps increasing
    time.sleep(0.01)
    assert e.duration > duration


def test_json_formatter_with_event():
    """JSON formatter includes event context."""
    import json
    
    messages = []
    
    class CaptureHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.formatter = ErgoJSONFormatter()
        
        def emit(self, record):
            messages.append(self.format(record))
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        with eg.tag(request_id='xyz'):
            with eg.event(user='json_user') as e:
                e.set(action='json_test')
        
        assert len(messages) == 1
        obj = json.loads(messages[0])
        assert obj['event']['user'] == 'json_user'
        assert obj['event']['action'] == 'json_test'
        assert obj['event']['tags']['request_id'] == 'xyz'
        assert 'duration_s' in obj
    finally:
        eg._logger.removeHandler(handler)


def test_json_formatter_with_regular_log():
    """JSON formatter works with regular logs (no event)."""
    import json
    
    messages = []
    
    class CaptureHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.formatter = ErgoJSONFormatter()
        
        def emit(self, record):
            messages.append(self.format(record))
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        with eg.tag(user='tag_user'):
            eg.info('regular log message')
        
        assert len(messages) == 1
        obj = json.loads(messages[0])
        assert obj['message'] == 'regular log message'
        assert obj['tags']['user'] == 'tag_user'
        assert 'event' not in obj  # No event context
    finally:
        eg._logger.removeHandler(handler)


def test_event_with_override_context():
    """emit() can override context."""
    messages = []
    
    class CaptureHandler(logging.Handler):
        def emit(self, record):
            messages.append(record)
    
    handler = CaptureHandler()
    eg._logger.addHandler(handler)
    
    try:
        e = eg.event(user='original')
        e.emit(user='overridden')
        
        assert len(messages) == 1
        assert messages[0].event['user'] == 'overridden'
    finally:
        eg._logger.removeHandler(handler)