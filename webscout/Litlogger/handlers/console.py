import sys
from typing import TextIO
from ..core.level import LogLevel

class ConsoleHandler:
    def __init__(
        self,
        level: LogLevel = LogLevel.NOTSET,
        stream: TextIO = sys.stdout,
        colors: bool = True
    ):
        self.level = level
        self.stream = stream
        self.colors = colors

    def emit(self, message: str, level: LogLevel):
        """Write log message to console with enhanced formatting."""
        if self.level == LogLevel.NOTSET or level.value >= self.level.value:
            try:
                # Add a newline if message doesn't end with one
                if not message.endswith('\n'):
                    message += '\n'
                
                self.stream.write(message)
                self.stream.flush()
            except Exception as e:
                # Fallback to stderr on error
                sys.stderr.write(f"Error in ConsoleHandler: {e}\n")
                sys.stderr.write(message)
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
