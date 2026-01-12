"""
Enhanced Logger for the Document Agent System.

Provides structured logging with configurable levels,
file and console output, and JSON formatting option.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


# Configure log directory and file
LOG_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Get log level from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def setup_logging(
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
    console_output: bool = True,
    json_format: bool = False
) -> logging.Logger:
    """
    Set up the application logger with configurable options.
    
    Args:
        log_file: Path to log file (default: app.log in utils directory)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output to console
        json_format: Whether to use JSON format for log messages
        
    Returns:
        Configured logger instance
    """
    log_file = log_file or LOG_FILE
    log_level = log_level or LOG_LEVEL
    
    # Create logger
    logger = logging.getLogger("DocumentAgent")
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "extra"):
            log_entry["extra"] = record.extra
        
        return json.dumps(log_entry)


# Create default logger
_default_logger: Optional[logging.Logger] = None


def _get_logger() -> logging.Logger:
    """Get or create the default logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging()
    return _default_logger


def log_info(message: str) -> None:
    """Log an info message."""
    _get_logger().info(message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    _get_logger().warning(message)


def log_error(message: str) -> None:
    """Log an error message."""
    _get_logger().error(message)


def log_debug(message: str) -> None:
    """Log a debug message."""
    _get_logger().debug(message)


def log_critical(message: str) -> None:
    """Log a critical message."""
    _get_logger().critical(message)


def log_exception(message: str) -> None:
    """Log an exception with traceback."""
    _get_logger().exception(message)


# Also support the legacy basicConfig approach for backward compatibility
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
