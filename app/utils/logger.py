#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logging utility for the WydBot application.
Sets up logging with file and console handlers.
"""

import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


# Log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# Default log location
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "wydbot.log"


def setup_logger(
    name: str = "wydbot",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    max_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_size: Maximum log file size in bytes
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Set log level
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = DEFAULT_LOG_FILE
    
    # Create log directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized at level {level}")
    
    return logger


class LoggerWrapper:
    """
    Wrapper for the standard logging module.
    Provides a consistent interface for logging.
    """
    
    def __init__(self, name: Optional[str] = None, level: int = logging.INFO):
        """
        Initialize the logger wrapper.
        
        Args:
            name: The logger name
            level: The logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self.logger.debug(message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """Log an info message."""
        self.logger.info(message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self.logger.warning(message, **kwargs)
        
    def error(self, message: str, **kwargs):
        """Log an error message."""
        self.logger.error(message, **kwargs)
        
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str) -> None:
        """Log an exception message."""
        self.logger.exception(message)
    
    def start_timer(self, name: str) -> None:
        """Start a timer for performance tracking."""
        self._start_times[name] = datetime.now()
    
    def end_timer(self, name: str, level: str = "DEBUG") -> float:
        """
        End a timer and log the elapsed time.
        
        Args:
            name: Timer name
            level: Log level to use
            
        Returns:
            Elapsed time in seconds
        """
        if name not in self._start_times:
            self.warning(f"Timer {name} was not started")
            return 0.0
        
        end_time = datetime.now()
        elapsed = (end_time - self._start_times[name]).total_seconds()
        
        log_method = getattr(self, level.lower(), self.debug)
        log_method(f"{name} completed in {elapsed:.3f} seconds")
        
        del self._start_times[name]
        return elapsed 