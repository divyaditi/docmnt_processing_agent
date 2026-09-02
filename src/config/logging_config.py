"""
Centralized logging configuration for the application.
Console-only logging for development and debugging.
"""
import logging
import sys


def setup_logging(log_level=logging.INFO):
    """
    Configure logging for the entire application.
    Logs to console with detailed format.
    
    Args:
        log_level: The logging level (default: INFO)
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console formatter with detailed information
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler - Main logging output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Log initial message
    root_logger.info("=" * 80)
    root_logger.info("Logging initialized successfully - Console logging enabled")
    root_logger.info("=" * 80)
