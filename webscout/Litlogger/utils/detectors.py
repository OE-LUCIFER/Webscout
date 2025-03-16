import re
import sys
from typing import Optional
from ..core.level import LogLevel

class LevelDetector:
    """Utility class for intelligent log level detection."""
    
    # Common patterns indicating error conditions
    ERROR_PATTERNS = [
        r"error",
        r"exception",
        r"failed",
        r"failure",
        r"traceback",
        r"crash",
        r"fatal",
    ]
    
    # Common patterns indicating warning conditions
    WARNING_PATTERNS = [
        r"warning",
        r"warn",
        r"deprecated",
        r"might",
        r"consider",
        r"attention",
    ]
    
    # Common patterns indicating debug information
    DEBUG_PATTERNS = [
        r"debug",
        r"trace",
        r"verbose",
        r"detail",
    ]
    
    @classmethod
    def detect_level(cls, message: str, exception: Optional[Exception] = None) -> LogLevel:
        """
        Detect appropriate log level from message content and context.
        
        Args:
            message: Log message to analyze
            exception: Optional exception object
            
        Returns:
            Detected LogLevel
        """
        # If there's an exception, it's at least ERROR
        if exception is not None:
            if isinstance(exception, (SystemExit, KeyboardInterrupt)):
                return LogLevel.CRITICAL
            return LogLevel.ERROR
            
        # Convert to lowercase for pattern matching
        message_lower = message.lower()
        
        # Check for error patterns
        for pattern in cls.ERROR_PATTERNS:
            if re.search(pattern, message_lower):
                return LogLevel.ERROR
                
        # Check for warning patterns
        for pattern in cls.WARNING_PATTERNS:
            if re.search(pattern, message_lower):
                return LogLevel.WARNING
                
        # Check for debug patterns
        for pattern in cls.DEBUG_PATTERNS:
            if re.search(pattern, message_lower):
                return LogLevel.DEBUG
                
        # Default to INFO
        return LogLevel.INFO
        
    @classmethod
    def detect_level_from_exception(cls, exc_type, exc_value, exc_tb) -> LogLevel:
        """
        Detect log level from exception information.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_tb: Exception traceback
            
        Returns:
            Detected LogLevel
        """
        # Critical errors that should terminate execution
        if exc_type in (SystemExit, KeyboardInterrupt, MemoryError):
            return LogLevel.CRITICAL
            
        # Built-in exceptions that indicate programming errors
        if exc_type in (
            SyntaxError,
            IndentationError,
            NameError,
            TypeError,
            AttributeError
        ):
            return LogLevel.ERROR
            
        # Runtime errors that might be recoverable
        if exc_type in (
            ValueError,
            KeyError,
            IOError,
            OSError,
            ConnectionError
        ):
            return LogLevel.WARNING
            
        # Default to ERROR for unknown exception types
        return LogLevel.ERROR

    @classmethod
    def detect_level_from_frame(cls, frame_depth: int = 1) -> LogLevel:
        """
        Detect log level by analyzing the call stack.
        
        Args:
            frame_depth: How many frames up to look (1 = caller's frame)
            
        Returns:
            Detected LogLevel
        """
        try:
            frame = sys._getframe(frame_depth)
            
            # Check function/method name
            code = frame.f_code
            func_name = code.co_name.lower()
            
            if any(p in func_name for p in ["error", "fail", "crash"]):
                return LogLevel.ERROR
            if any(p in func_name for p in ["warn"]):
                return LogLevel.WARNING
            if any(p in func_name for p in ["debug", "trace"]):
                return LogLevel.DEBUG
                
            # Check local variables for exceptions
            locals_dict = frame.f_locals
            for value in locals_dict.values():
                if isinstance(value, Exception):
                    return cls.detect_level_from_exception(
                        type(value), value, value.__traceback__
                    )
                    
            return LogLevel.INFO
            
        except Exception:
            return LogLevel.INFO  # Default if detection fails
