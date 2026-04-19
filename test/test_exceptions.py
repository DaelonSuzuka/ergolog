"""Tests that ergolog constructs clean up properly when exceptions occur."""

from pytest import LogCaptureFixture

from ergolog import eg
from ergolog.ergolog import ErgoTagger


class CustomError(Exception):
    pass


# --- Tags ---


def test_tag_context_cleans_up_on_exception(caplog: LogCaptureFixture):
    """Tag stack must be empty after an exception inside a tag context."""

    try:
        with eg.tag('should_be_removed'):
            raise CustomError('boom')
    except CustomError:
        pass

    assert ErgoTagger._tag_stack_var.get() == []


def test_nested_tag_cleanup_on_exception():
    """All nested tag contexts must unwind correctly on exception.
    Exception propagates through all contexts, so all tags are removed."""

    try:
        with eg.tag('outer'):
            with eg.tag('middle'):
                with eg.tag('inner'):
                    raise CustomError('boom')
    except CustomError:
        pass

    assert ErgoTagger._tag_stack_var.get() == []


def test_tag_decorator_cleans_up_on_exception():
    """Tag decorator must clean up even when the decorated function raises."""

    @eg.tag('failing')
    def failing_func():
        raise CustomError('boom')

    try:
        failing_func()
    except CustomError:
        pass

    assert ErgoTagger._tag_stack_var.get() == []


def test_outer_tag_survives_inner_exception():
    """When an inner tag context raises and the exception is caught
    inside the outer context, the outer tag should remain on the stack."""

    with eg.tag('outer'):
        try:
            with eg.tag('inner'):
                raise CustomError('boom')
        except CustomError:
            pass
        # inner is cleaned up, outer is still active
        assert ErgoTagger._tag_stack_var.get() == ['outer']

    # both cleaned up now
    assert ErgoTagger._tag_stack_var.get() == []


# --- Timers ---


def test_timer_callback_on_exception():
    """Timer callback should fire even when the timed block raises."""

    results = []

    try:
        with eg.timer(lambda t: results.append(t)):
            raise CustomError('boom')
    except CustomError:
        pass

    assert len(results) == 1
    assert float(results[0]) >= 0


def test_timer_context_manager_repr_on_exception():
    """Timer __repr__ should still work after an exception inside the context."""

    try:
        with eg.timer() as t:
            raise CustomError('boom')
    except CustomError:
        pass

    # t is still bound and has a repr
    assert float(repr(t)) >= 0


def test_timer_decorator_callback_on_exception():
    """Timer decorator callback should fire even when the function raises."""

    results = []

    @eg.timer(lambda t: results.append(t))
    def failing_func():
        raise CustomError('boom')

    try:
        failing_func()
    except CustomError:
        pass

    assert len(results) == 1


# --- Trace ---


def test_trace_cleans_up_on_exception():
    """Trace should clean up its tag context when the function raises."""

    @eg.trace()
    def failing_func():
        raise CustomError('boom')

    try:
        failing_func()
    except CustomError:
        pass

    assert ErgoTagger._tag_stack_var.get() == []


def test_trace_log_args_cleans_up_on_exception():
    """Trace with log_args should clean up when the function raises."""

    @eg.trace(log_args=True)
    def failing_func(x):
        raise CustomError('boom')

    try:
        failing_func(42)
    except CustomError:
        pass

    assert ErgoTagger._tag_stack_var.get() == []