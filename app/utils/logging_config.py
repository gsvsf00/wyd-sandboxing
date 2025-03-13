"""
Logging Configuration Module

Provides centralized logging configuration for the WydBot application.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional

# Default log folder
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Singleton logger dictionary
_loggers = {}

def setup_logging(
    log_dir: str = LOG_DIR,
    log_level: int = logging.INFO,
    console_level: int = logging.INFO,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    max_size: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 5
) -> None:
    """
    Set up logging for the application.
    
    Args:
        log_dir: Directory to store log files
        log_level: Log level for file handler
        console_level: Log level for console handler
        log_format: Log format
        date_format: Date format
        max_size: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(log_format, date_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all logs to be filtered by handlers
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create and add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create and add file handler (with rotation)
    log_file = os.path.join(log_dir, "wydbot.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Log startup message
    root_logger.info(f"Logging initialized at {datetime.now()}")
    root_logger.info(f"Log file: {log_file}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger

class LoggerWrapper:
    """
    Wrapper class for consistent logging throughout the application.
    Provides additional context and utility methods.
    """
    
    def __init__(self, name: str = None):
        """
        Initialize the logger wrapper.
        
        Args:
            name: Logger name
        """
        self.logger = get_logger(name or self.__class__.__name__)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, exc_info=True, **kwargs):
        """Log exception message."""
        self.logger.exception(message, *args, exc_info=exc_info, **kwargs)

def set_global_log_level(level: str) -> None:
    """
    Set the log level for all existing loggers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Update all existing loggers
    for logger in _loggers.values():
        logger.setLevel(log_level)
        
        # Update handlers
        for handler in logger.handlers:
            handler.setLevel(log_level)
            
    logging.info(f"Global log level set to {level}")

def clear_loggers() -> None:
    """Clear all cached loggers."""
    _loggers.clear()
    logging.info("All loggers cleared") 