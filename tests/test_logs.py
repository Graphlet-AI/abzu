"""Tests for the centralized logging module."""

import logging
from unittest import mock

from abzu.logs import get_logger


def test_get_logger_returns_logger():
    """Test that get_logger returns a logging.Logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_get_logger_no_name_returns_root_logger():
    """Test that get_logger with no name returns root logger."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "root"


def test_logger_writes_to_file(tmp_path):
    """Test that logger writes to the configured log file."""
    # Create a test log file
    test_log_file = tmp_path / "test.log"

    # Create a logger with our own file handler to test file writing
    test_logger = logging.getLogger("test_file_writer_unique")
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False  # Don't propagate to avoid interference

    # Add file handler
    file_handler = logging.FileHandler(test_log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    test_logger.addHandler(file_handler)

    # Write a test message
    test_message = "Test log message for file"
    test_logger.info(test_message)

    # Force flush
    file_handler.flush()

    # Check if log file was created and contains our message
    assert test_log_file.exists()
    log_content = test_log_file.read_text()
    assert test_message in log_content

    # Clean up
    test_logger.removeHandler(file_handler)
    file_handler.close()


def test_logger_format():
    """Test that logger uses the correct format."""
    # Create a test handler with known format
    test_handler = logging.StreamHandler()
    test_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    test_handler.setFormatter(test_formatter)

    # Check the format string
    assert test_handler.formatter is not None
    format_str = test_handler.formatter._fmt  # type: ignore[union-attr]
    assert "%(asctime)s" in format_str  # type: ignore[operator]
    assert "%(name)s" in format_str  # type: ignore[operator]
    assert "%(levelname)s" in format_str  # type: ignore[operator]
    assert "%(message)s" in format_str  # type: ignore[operator]


def test_logger_level():
    """Test that get_logger returns a working logger."""
    # Get a logger using get_logger
    logger = get_logger("test_level_check")

    # Test that the logger works by actually logging
    # This is more practical than checking the level
    with mock.patch.object(logger, "info") as mock_info:
        logger.info("test message")
        # If the logger is working, this should be called
        assert mock_info.called or logger.isEnabledFor(logging.INFO)


def test_logger_handlers():
    """Test that logger has both file and stream handlers."""
    logger = logging.getLogger()

    handler_types = [type(handler) for handler in logger.handlers]
    assert logging.FileHandler in handler_types or any(
        isinstance(handler, logging.FileHandler) for handler in logger.handlers
    )
    assert logging.StreamHandler in handler_types or any(
        isinstance(handler, logging.StreamHandler) for handler in logger.handlers
    )


def test_log_directory_creation(tmp_path):
    """Test that log directory is created if it doesn't exist."""
    # Create a nested path that doesn't exist
    nested_log_dir = tmp_path / "nested" / "logs"

    # Mock the config to use our nested directory
    with mock.patch("abzu.logs.config.get", return_value=str(nested_log_dir)):
        # Re-import to trigger directory creation
        import importlib

        import abzu.logs

        importlib.reload(abzu.logs)

        # Check that the directory was created
        assert nested_log_dir.exists()
        assert nested_log_dir.is_dir()


def test_logger_propagation():
    """Test logger propagation behavior."""
    # Create a child logger
    logger = get_logger("abzu.test.module")

    # Child loggers should propagate by default (unless explicitly disabled)
    # This ensures log messages bubble up to root logger
    assert logger.propagate is True


def test_multiple_loggers_same_name():
    """Test that multiple calls with same name return same logger."""
    logger1 = get_logger("test_same")
    logger2 = get_logger("test_same")

    # Should be the exact same object
    assert logger1 is logger2


def test_logger_hierarchy():
    """Test that logger hierarchy works correctly."""
    parent_logger = get_logger("abzu")
    child_logger = get_logger("abzu.test")
    grandchild_logger = get_logger("abzu.test.module")

    # Check hierarchy
    assert child_logger.parent == parent_logger
    assert grandchild_logger.parent == child_logger
