import sys
from ..core.level import LogLevel
from ..styles.colors import LogColors

class ConsoleHandler:
    def __init__(self, level: LogLevel = LogLevel.DEBUG, stream=sys.stdout):
        self.level = level
        self.stream = stream
        self.colors = LogColors()

    def emit(self, message: str, level: LogLevel):
        """Write the colored message to the console."""
        try:
            # Apply color based on log level
            color = LogColors.LEVEL_COLORS.get(level, LogColors.RESET)
            colored_message = f"{color}{message}{LogColors.RESET}"
            print(colored_message, file=self.stream, flush=True)
        except Exception as e:
            # Fallback to plain printing if coloring fails
            print(message, file=self.stream, flush=True)

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
