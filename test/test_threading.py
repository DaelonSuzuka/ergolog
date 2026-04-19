"""Tests that demonstrate thread-safety issues with the shared tag_stack.

Run with: uv run pytest test/test_threading.py -v

These tests are designed to expose race conditions in the current
implementation where ErgoTagger.tag_stack is a single shared list
across all threads.
"""

import logging
import threading
from time import sleep

from ergolog import eg
from ergolog.ergolog import ErgoTagger


class TagRecorder(logging.Handler):
    """A handler that records the .tags attribute of each LogRecord."""

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        # Force formatting so record.tags gets populated
        self.format(record)
        self.records.append(record)


def _add_recorder() -> TagRecorder:
    """Attach a TagRecorder to the root ergo logger and return it."""
    handler = TagRecorder()
    handler.setLevel(logging.DEBUG)
    eg._logger.addHandler(handler)
    # Set logger to DEBUG to ensure messages are processed
    eg._logger.setLevel(logging.DEBUG)
    return handler


def _remove_recorder(handler: TagRecorder):
    """Detach a TagRecorder from the root ergo logger."""
    eg._logger.removeHandler(handler)


def test_two_threads_tags_dont_leak():
    """Two threads each set a unique tag. Each should only see its own tag.

    With the current shared tag_stack, both threads will see [AAA, BBB]
    because both tags are on the same list simultaneously.
    """

    handler = _add_recorder()

    barrier = threading.Barrier(2)
    results: dict[str, str] = {}
    errors: list[Exception] = []

    def thread_fn(tag_name: str):
        try:
            with eg.tag(tag_name):
                # Wait until BOTH threads are inside their tag blocks
                barrier.wait()
                sleep(0.05)  # give a window where both are active
                eg.info(f'message from {tag_name}')
                # Find the last record we just emitted
                for rec in reversed(handler.records):
                    if rec.message == f'message from {tag_name}':
                        results[tag_name] = rec.tags
                        break
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=thread_fn, args=('AAA',))
    t2 = threading.Thread(target=thread_fn, args=('BBB',))

    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)

    _remove_recorder(handler)

    for e in errors:
        raise e

    tag_a = results.get('AAA', 'MISSING')
    tag_b = results.get('BBB', 'MISSING')

    print(f'Thread AAA saw tags: {tag_a!r}')
    print(f'Thread BBB saw tags: {tag_b!r}')

    # With shared tag_stack, one or both will see both tags
    assert tag_a == '[AAA] ', f'Thread AAA saw tags: {tag_a!r}, expected "[AAA] " — tag leaked from other thread'
    assert tag_b == '[BBB] ', f'Thread BBB saw tags: {tag_b!r}, expected "[BBB] " — tag leaked from other thread'


def test_parallel_tag_depth():
    """Two threads nest tags to different depths. Each should see only its own chain.

    With shared tag_stack, the shallow thread might pick up tags from the
    deep thread, or vice versa.
    """

    handler = _add_recorder()

    barrier = threading.Barrier(2)
    results: dict[str, str] = {}
    errors: list[Exception] = []

    def shallow_thread():
        try:
            with eg.tag('S'):
                barrier.wait()
                sleep(0.05)
                eg.info('shallow')
                for rec in reversed(handler.records):
                    if rec.message == 'shallow':
                        results['shallow'] = rec.tags
                        break
        except Exception as e:
            errors.append(e)

    def deep_thread():
        try:
            with eg.tag('D1'):
                with eg.tag('D2'):
                    with eg.tag('D3'):
                        barrier.wait()
                        sleep(0.05)
                        eg.info('deep')
                        for rec in reversed(handler.records):
                            if rec.message == 'deep':
                                results['deep'] = rec.tags
                                break
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=shallow_thread)
    t2 = threading.Thread(target=deep_thread)

    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)

    _remove_recorder(handler)

    for e in errors:
        raise e

    shallow_tags = results.get('shallow', 'MISSING')
    deep_tags = results.get('deep', 'MISSING')

    print(f'Shallow thread saw tags: {shallow_tags!r}')
    print(f'Deep thread saw tags: {deep_tags!r}')

    assert shallow_tags == '[S] ', f'Shallow saw {shallow_tags!r}, expected "[S] "'
    assert deep_tags == '[D1, D2, D3] ', f'Deep saw {deep_tags!r}, expected "[D1, D2, D3] "'


def test_tag_stack_corruption_on_exit():
    """When two threads enter/exit tags concurrently, list.remove() can remove
    the wrong thread's tag, leaving the stack in a corrupted state.

    Thread 1 pushes A, Thread 2 pushes B.
    Thread 1 exits -> list.remove('A') works, stack is [B]. Fine.
    But if Thread 2 exits first -> list.remove('B') works, stack is [A].
    Then Thread 1 exits -> list.remove('A') works. Stack is [].
    BUT: if both push the SAME TAG NAME, list.remove() will pop the FIRST
    occurrence, which may belong to the other thread.
    """

    handler = _add_recorder()

    barrier = threading.Barrier(2)
    results: dict[str, str] = {}
    errors: list[Exception] = []

    def thread_fn(thread_id: str, barrier: threading.Barrier):
        try:
            # Both threads use the SAME tag name — this exposes list.remove() bug
            with eg.tag('shared_tag'):
                barrier.wait()
                sleep(0.05)
                eg.info(f'msg from {thread_id}')
                for rec in reversed(handler.records):
                    if rec.message == f'msg from {thread_id}':
                        results[thread_id] = rec.tags
                        break
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=thread_fn, args=('T1', barrier))
    t2 = threading.Thread(target=thread_fn, args=('T2', barrier))

    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)

    _remove_recorder(handler)

    for e in errors:
        raise e

    # After both threads exit, the tag_stack should be empty
    print(f'Tag stack after both threads exit: {ErgoTagger._tag_stack_var.get()!r}')
    print(f'T1 saw tags: {results.get("T1", "MISSING")!r}')
    print(f'T2 saw tags: {results.get("T2", "MISSING")!r}')

    # Both threads pushed 'shared_tag' twice, so stack had ['shared_tag', 'shared_tag']
    # Both called list.remove('shared_tag') which removes the FIRST occurrence.
    # This actually works by accident for 2 identical tags.
    # But the real test: when they log, they should each see [shared_tag, shared_tag]
    # because BOTH copies are on the stack. A thread-local solution would show [shared_tag].

    # The key assertion: after both threads are done, the stack must be empty
    assert ErgoTagger._tag_stack_var.get() == [], f'Tag stack should be empty but is: {ErgoTagger._tag_stack_var.get()!r}'

    # And each thread should only see ONE 'shared_tag', not two
    for tid in ('T1', 'T2'):
        tags = results.get(tid, 'MISSING')
        assert tags == '[shared_tag] ', f'Thread {tid} saw {tags!r}, expected "[shared_tag] "'