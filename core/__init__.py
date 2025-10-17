"""
Core module - Contains foundational utilities and configurations
"""

# Database utilities
from .database import (
    Base,
    get_async_db,
    init_db,
    create_tables,
    drop_tables
)

# Logging utilities  
from .logger import (
    LOGGERS,
    setup_loggers,
    get_database_logger,
    get_debug_logger,
    get_error_logger,
    log_database_operation,
    log_error,
    log_debug
)

# Full module
__all__ = [
    # Database
    "Base",
    "get_async_db",
    "init_db",
    "create_tables",
    "drop_tables",
    
    # Logging
    "LOGGERS",
    "setup_loggers",
    "get_database_logger",
    "get_debug_logger", 
    "get_error_logger",
    "log_database_operation",
    "log_error",
    "log_debug"
]