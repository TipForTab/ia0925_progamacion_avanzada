import logging
import logging.handlers
from pathlib import Path
from typing import Dict


LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

def setup_loggers() -> Dict[str, logging.Logger]:
    """
    Setup multiple loggers for different purposes
    Returns a dictionary with configured loggers
    """
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    loggers = {}

    debug_logger = logging.getLogger('debug')
    debug_logger.setLevel(logging.DEBUG)
    
    debug_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / 'debug.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    debug_handler.setFormatter(formatter)
    debug_logger.addHandler(debug_handler)
    loggers['debug'] = debug_logger

    error_logger = logging.getLogger('error')
    error_logger.setLevel(logging.ERROR)
    
    error_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / 'error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10  # Keep more error logs
    )
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    loggers['error'] = error_logger
    return loggers

LOGGERS = setup_loggers()

def get_debug_logger() -> logging.Logger:
    """Get the debug logger"""
    return LOGGERS['debug']

def get_error_logger() -> logging.Logger:
    """Get the error logger"""
    return LOGGERS['error']

def log_error(error: Exception, context: str = ""):
    """Log errors with context"""
    get_error_logger().error(f"{context}: {str(error)}", exc_info=True)

def log_debug(message: str, extra_data: dict = None):
    """Log debug information"""
    if extra_data:
        message += f" | Data: {extra_data}"
    get_debug_logger().debug(message)