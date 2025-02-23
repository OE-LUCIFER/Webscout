import sys
from typing import Optional, TextIO
from ..core.level import LogLevel

class ConsoleHandler:
    """Handler for outputting log messages to the console."""
    
    def __init__(self, 
                 stream: Optional[TextIO] = None,
                 level: LogLevel = LogLevel.DEBUG):
        """
        Initialize console handler.
        
        Args:
            stream: Output stream (defaults to sys.stdout)
            level: Minimum log level to output
        """
        self.stream = stream or sys.stdout
        self.level = level
        
    def emit(self, message: str, level: LogLevel):
        """
        Write log message to console if level is sufficient.
        
        Args:
            message: Formatted log message
            level: Message log level
        """
        if level.value >= self.level.value:
            try:
                self.stream.write(message + "\n")
                self.stream.flush()
            except Exception as e:
                # Fallback to stderr on error
                sys.stderr.write(f"Error in ConsoleHandler: {e}\n")
                sys.stderr.write(message + "\n")
                sys.stderr.flush()

    async def async_emit(self, message: str, level: LogLevel):
        """
        Asynchronously write log message to console.
        Just calls emit() since console output is generally fast enough.
        """
        self.emit(message, level)

class ErrorConsoleHandler(ConsoleHandler):
    """Specialized handler that writes to stderr."""
    
    def __init__(self, level: LogLevel = LogLevel.ERROR):
        super().__init__(stream=sys.stderr, level=level)
