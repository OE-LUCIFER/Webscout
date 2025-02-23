"""
LitLogger - A feature-rich, colorful logging library with intelligent level detection.

Features:
- Colorful console output
- Multiple output formats including JSON
- File logging with rotation
- Network logging (HTTP/HTTPS/TCP)
- Async logging support
- Intelligent log level detection
- Context managers
- Performance metrics
- Log aggregation
"""

from .core.logger import Logger
from .core.level import LogLevel
from .styles.colors import LogColors
from .styles.formats import LogFormat
from .styles.text import TextStyle
from .handlers.console import ConsoleHandler, ErrorConsoleHandler
from .handlers.file import FileHandler
from .handlers.network import NetworkHandler
from .utils.detectors import LevelDetector
from .utils.formatters import MessageFormatter

# Create a default logger instance
default_logger = Logger(
    name="LitLogger",
    handlers=[ConsoleHandler()]
)

# Expose common logging methods at package level
debug = default_logger.debug
info = default_logger.info
warning = default_logger.warning
error = default_logger.error
critical = default_logger.critical

__all__ = [
    # Core
    "Logger",
    "LogLevel",
    
    # Styles
    "LogColors",
    "LogFormat",
    "TextStyle",
    
    # Handlers
    "ConsoleHandler",
    "ErrorConsoleHandler", 
    "FileHandler",
    "NetworkHandler",
    
    # Utils
    "LevelDetector",
    "MessageFormatter",
    
    # Package-level logging functions
    "debug",
    "info",
    "warning",
    "error",
    "critical",

]
