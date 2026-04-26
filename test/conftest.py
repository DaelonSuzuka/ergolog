import logging
import pytest


@pytest.fixture(autouse=True)
def _restore_ergolog():
    """Ensure ergolog handler is restored after any test that modifies it.

    Some tests (e.g., test_config.py) remove all handlers to test configuration
    in isolation. This fixture ensures the default handler is restored afterward.
    """
    logger = logging.getLogger('ergo')
    # Save state before test
    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate

    yield

    # Restore state after test
    logger.handlers.clear()
    for handler in original_handlers:
        logger.addHandler(handler)
    logger.setLevel(original_level)
    logger.propagate = original_propagate