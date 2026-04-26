"""Tests for ErgoConfig — the runtime configuration API."""

import logging
import pytest
from ergolog import eg, ErgoConfig


@pytest.fixture
def clean_logger():
    """Remove all handlers from the ergo logger for testing in isolation."""
    logger = logging.getLogger('ergo')
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    logger.setLevel(logging.NOTSET)


class TestConfigAPI:
    """Test that eg.config is an ErgoConfig instance and has the right methods."""

    def test_config_is_attached_to_eg(self):
        assert isinstance(eg.config, ErgoConfig)

    def test_config_has_add_output(self):
        assert callable(eg.config.add_output)

    def test_config_has_remove_output(self):
        assert callable(eg.config.remove_output)

    def test_config_has_set_format(self):
        assert callable(eg.config.set_format)


class TestAddOutput:
    """Test adding output handlers."""

    def test_add_stdout_handler(self, clean_logger):
        logger = logging.getLogger('ergo')
        assert len(logger.handlers) == 0

        eg.config.add_output('stdout', format='default')

        assert len(logger.handlers) == 1
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)

    def test_add_stderr_handler(self, clean_logger):
        logger = logging.getLogger('ergo')

        eg.config.add_output('stderr', format='default')

        assert len(logger.handlers) == 1
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)

    def test_add_file_handler(self, clean_logger, tmp_path):
        logger = logging.getLogger('ergo')
        log_file = str(tmp_path / 'test.jsonl')

        eg.config.add_output('file', path=log_file, format='json')

        assert len(logger.handlers) == 1
        handler = logger.handlers[0]
        assert isinstance(handler, logging.FileHandler)
        handler.close()

    def test_add_json_format(self, clean_logger):
        from ergolog import ErgoJSONFormatter

        eg.config.add_output('stdout', format='json')

        handler = logging.getLogger('ergo').handlers[0]
        assert isinstance(handler.formatter, ErgoJSONFormatter)

    def test_add_default_format(self, clean_logger):
        from ergolog import ErgoFormatter

        eg.config.add_output('stdout', format='default')

        handler = logging.getLogger('ergo').handlers[0]
        assert isinstance(handler.formatter, ErgoFormatter)

    def test_add_output_sets_logger_level(self, clean_logger):
        logger = logging.getLogger('ergo')
        assert logger.level == logging.NOTSET

        eg.config.add_output('stdout', format='default')

        assert logger.level == logging.DEBUG

    def test_add_output_does_not_override_existing_level(self, clean_logger):
        logger = logging.getLogger('ergo')
        logger.setLevel(logging.WARNING)

        eg.config.add_output('stdout', format='default')

        assert logger.level == logging.WARNING

    def test_add_output_replaces_same_name(self, clean_logger):
        eg.config.add_output('stdout', format='default')
        assert len(logging.getLogger('ergo').handlers) == 1

        eg.config.add_output('stdout', format='json')
        assert len(logging.getLogger('ergo').handlers) == 1

    def test_add_multiple_outputs(self, clean_logger, tmp_path):
        log_file = str(tmp_path / 'test.jsonl')

        eg.config.add_output('stdout', format='default')
        eg.config.add_output('file', path=log_file, format='json')

        assert len(logging.getLogger('ergo').handlers) == 2
        # Clean up file handler
        for h in logging.getLogger('ergo').handlers:
            h.close()

    def test_invalid_kind_raises(self, clean_logger):
        with pytest.raises(ValueError, match="Invalid output kind"):
            eg.config.add_output('network')

    def test_invalid_format_raises(self, clean_logger):
        with pytest.raises(ValueError, match="Invalid format"):
            eg.config.add_output('stdout', format='xml')


class TestRemoveOutput:
    """Test removing output handlers."""

    def test_remove_stdout(self, clean_logger):
        eg.config.add_output('stdout', format='default')
        assert len(logging.getLogger('ergo').handlers) == 1

        eg.config.remove_output('stdout')
        assert len(logging.getLogger('ergo').handlers) == 0

    def test_remove_file_handler(self, clean_logger, tmp_path):
        log_file = str(tmp_path / 'test.jsonl')

        eg.config.add_output('file', path=log_file, format='json')
        assert len(logging.getLogger('ergo').handlers) == 1

        eg.config.remove_output('file', path=log_file)
        assert len(logging.getLogger('ergo').handlers) == 0


class TestSetFormat:
    """Test changing formatter on existing handlers."""

    def test_change_to_json(self, clean_logger):
        from ergolog import ErgoJSONFormatter

        eg.config.add_output('stdout', format='default')
        eg.config.set_format('json', kind='stdout')

        handler = logging.getLogger('ergo').handlers[0]
        assert isinstance(handler.formatter, ErgoJSONFormatter)

    def test_change_to_default(self, clean_logger):
        from ergolog import ErgoFormatter

        eg.config.add_output('stdout', format='json')
        eg.config.set_format('default', kind='stdout')

        handler = logging.getLogger('ergo').handlers[0]
        assert isinstance(handler.formatter, ErgoFormatter)


class TestAutoSetup:
    """Test the auto-setup behavior."""

    def test_auto_setup_adds_handler(self, clean_logger):
        config = ErgoConfig()
        config.auto_setup()

        logger = logging.getLogger('ergo')
        assert len(logger.handlers) == 1

    def test_auto_setup_idempotent(self, clean_logger):
        config = ErgoConfig()
        config.auto_setup()
        config.auto_setup()

        logger = logging.getLogger('ergo')
        assert len(logger.handlers) == 1

    def test_auto_setup_skips_if_handlers_exist(self, clean_logger):
        logger = logging.getLogger('ergo')
        # Add a dummy handler
        handler = logging.StreamHandler()
        logger.addHandler(handler)

        config = ErgoConfig()
        config.auto_setup()

        # Should still only have the one handler we added
        assert len(logger.handlers) == 1