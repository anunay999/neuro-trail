import logging
import sys
from logging.handlers import RotatingFileHandler
import os
from typing import Optional

from app.core.config import settings


def setup_logging(log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application
    
    Args:
        log_file: Optional path to log file
    """
    # Create logs directory if it doesn't exist
    log_dir = "./.logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Default log file
    if log_file is None:
        log_file = os.path.join(log_dir, "neurotrail.log")
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10485760, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Set specific levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)