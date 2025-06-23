"""Centralized logging configuration for python_template_project.

This module provides a unified logging setup that supports:
- File logging with rotation
- GUI integration via custom handler
- Configurable log levels from config
- Structured logging with consistent formatting
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from config_cli_gui.config import ConfigManager


class GuiLogHandler(logging.Handler):
    """Custom logging handler that can write to GUI text widgets."""

    def __init__(self, gui_writer=None):
        super().__init__()
        self.gui_writer = gui_writer
        self.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        )

    def emit(self, record):
        """Emit a log record to the GUI if writer is available."""
        if self.gui_writer:
            try:
                msg = self.format(record) + "\n"
                self.gui_writer.write(msg)
            except Exception:
                # Fail silently to avoid recursive logging errors
                pass


class LoggerManager:
    """Manages all logging configuration and handlers."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger("gpx_kml_converter")
        self.gui_handler = None
        self.file_handler = None
        self.console_handler = None
        self._setup_logging()

    def _setup_logging(self):
        """Configure all logging handlers and formatters."""
        # Clear any existing handlers
        self.logger.handlers.clear()

        # Set log level from config
        log_level = getattr(logging, self.config.get_category("app").log_level.default.upper())
        self.logger.setLevel(log_level)

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Setup file handler with rotation
        self._setup_file_handler(detailed_formatter)

        # Setup console handler
        self._setup_console_handler(simple_formatter)

        # Setup GUI handler (will be connected later if needed)
        self._setup_gui_handler()

    def _setup_file_handler(self, formatter):
        """Setup rotating file handler."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / "gpx_kml_converter.log"

        # Use RotatingFileHandler to prevent huge log files
        self.file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

    def _setup_console_handler(self, formatter):
        """Setup console handler for CLI output."""
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setFormatter(formatter)
        self.logger.addHandler(self.console_handler)

    def _setup_gui_handler(self):
        """Setup GUI handler (initially without writer)."""
        self.gui_handler = GuiLogHandler()
        # Don't add to logger yet - will be done when GUI connects

    def connect_gui_writer(self, gui_writer):
        """Connect a GUI writer to the logging system.

        Args:
            gui_writer: Object with write() method (like the LogHandler from gui.py)
        """
        if self.gui_handler:
            # Remove old handler if it exists
            if self.gui_handler in self.logger.handlers:
                self.logger.removeHandler(self.gui_handler)

        # Create new handler with GUI writer
        self.gui_handler = GuiLogHandler(gui_writer)
        self.logger.addHandler(self.gui_handler)

    def disconnect_gui_writer(self):
        """Disconnect GUI writer (useful when GUI closes)."""
        if self.gui_handler and self.gui_handler in self.logger.handlers:
            self.logger.removeHandler(self.gui_handler)

    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a logger instance.

        Args:
            name: Logger name (defaults to main project logger)

        Returns:
            Logger instance
        """
        if name:
            return logging.getLogger(f"gpx_kml_converter.{name}")
        return self.logger

    def set_log_level(self, level: str):
        """Change log level dynamically.

        Args:
            level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper())
        self.logger.setLevel(log_level)

        # Update config
        self.config.get_category("app").log_level.default = level.upper()

    def log_config_summary(self):
        """Log current configuration summary."""
        self.logger.info("=== Configuration Summary ===")
        self.logger.info(f"Log level: {self.config.get_category('app').log_level.default}")
        self.logger.info(f"Input: {self.config.get_category('cli').input.default}")
        self.logger.info(f"Output: {self.config.get_category('cli').output.default}")
        self.logger.info(f"Max workers: {self.config.get_category('app').max_workers.default}")
        self.logger.info("==============================")


# Global logger manager instance
_logger_manager = None


def initialize_logging(config: ConfigManager) -> LoggerManager:
    """Initialize the global logging system.

    Args:
        config: Configuration manager instance

    Returns:
        LoggerManager instance
    """
    global _logger_manager
    _logger_manager = LoggerManager(config)
    return _logger_manager


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (optional)

    Returns:
        Logger instance

    Raises:
        RuntimeError: If logging not initialized
    """
    if _logger_manager is None:
        raise RuntimeError("Logging not initialized. Call initialize_logging() first.")
    return _logger_manager.get_logger(name)


def get_logger_manager() -> LoggerManager:
    """Get the global logger manager.

    Returns:
        LoggerManager instance

    Raises:
        RuntimeError: If logging not initialized
    """
    if _logger_manager is None:
        raise RuntimeError("Logging not initialized. Call initialize_logging() first.")
    return _logger_manager


def connect_gui_logging(gui_writer):
    """Connect GUI writer to logging system.

    Args:
        gui_writer: GUI writer object with write() method
    """
    if _logger_manager:
        _logger_manager.connect_gui_writer(gui_writer)


def disconnect_gui_logging():
    """Disconnect GUI from logging system."""
    if _logger_manager:
        _logger_manager.disconnect_gui_writer()
