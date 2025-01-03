"""Logging configuration and utilities."""

import logging
from typing import Optional

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: The logging level to use
        log_file: Optional path to a log file
    """
    # Create logger
    logger = logging.getLogger('codefactory')
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Name for the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f'codefactory.{name}')
