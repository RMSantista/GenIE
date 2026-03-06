"""Logging configuration for GENIE framework."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure logging for the application.

    Sets up both console and file handlers with structured formatting.

    Args:
        log_level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Configured root logger

    The logger will output to both stdout and logs/genie.log file.
    Format includes timestamp, logger name, level, and message.
    """

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Format string with context information
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(
        log_dir / "genie.log",
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        logging.Logger: Configured logger for the module
    """

    return logging.getLogger(name)
