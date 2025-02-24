
import asyncio
import sys
import threading
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..core.level import LogLevel
from ..styles.formats import LogFormat
from ..styles.colors import LogColors

class Logger:
    # Emoji mappings for different log levels
    LEVEL_EMOJIS = {
        LogLevel.DEBUG: "🔍",
        LogLevel.INFO: "ℹ️",
        LogLevel.WARNING: "⚠️",
        LogLevel.ERROR: "❌",
        LogLevel.CRITICAL: "🔥"
    }

    def __init__(
        self,
        name: str = "LitLogger",
        level: Union[str, LogLevel, None] = None,  # Make level optional
        format: str = LogFormat.RICH,  # Change default format to RICH
        handlers: List = None,
        enable_colors: bool = True,  # Enable colors by default
        async_mode: bool = False,
        show_thread: bool = True,
        show_context: bool = True
    ):
        self.name = name
        # Set NOTSET as default if level is None
        self.level = LogLevel.NOTSET if level is None else (
            LogLevel.get_level(level) if isinstance(level, str) else level
        )
        self.format = format
        self.enable_colors = enable_colors
        self.async_mode = async_mode
        self.show_thread = show_thread
        self.show_context = show_context
        self._context_data = {}
        self._metrics = {}
        
        if not handlers:
            from ..handlers.console import ConsoleHandler
            handlers = [ConsoleHandler(level=LogLevel.NOTSET)]  # Set handler level to NOTSET
        self.handlers = handlers

    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on level."""
        return self.level == LogLevel.NOTSET or level.value >= self.level.value

    def _format_message(self, level: LogLevel, message: str, **kwargs) -> str:
        now = datetime.now()
        
        # Enhanced log data with new fields
        log_data = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "level": level.name,
            "level_colored": LogColors.level_style(level, f"[{level.name}]"),
            "name": self.name,
            "message": message,
            "emoji": self.LEVEL_EMOJIS.get(level, ""),
            "thread_info": f"[Thread: {threading.current_thread().name}]" if self.show_thread else "",
            "context": self._format_context() if self.show_context and self._context_data else "",
            "exception": self._format_exception(kwargs.get("exc_info")) if "exc_info" in kwargs else "",
            **self._context_data,
            **kwargs
        }

        try:
            formatted = self.format.format(**log_data)
            return formatted if not self.enable_colors else formatted
        except KeyError as e:
            # Fallback to basic format if formatting fails
            return f"[{log_data['time']}] {log_data['level_colored']}: {message}"

    def _format_context(self) -> str:
        """Format context data in a structured way."""
        if not self._context_data:
            return ""
        
        context_lines = ["\n│ Context:"]
        for key, value in self._context_data.items():
            context_lines.append(f"│   {key}: {value}")
        return "\n".join(context_lines)

    def _format_exception(self, exc_info) -> str:
        """Format exception information."""
        if not exc_info:
            return ""
        
        if isinstance(exc_info, bool):
            exc_info = sys.exc_info()
        
        if exc_info[0] is None:
            return ""
        
        formatted = "\n│ Exception:\n"
        formatted += "│ " + "\n│ ".join(traceback.format_exception(*exc_info))
        return formatted

    async def _async_log(self, level: LogLevel, message: str, **kwargs):
        # Log everything if level is NOTSET
        if self.level == LogLevel.NOTSET or level.value >= self.level.value:
            formatted_message = self._format_message(level, message, **kwargs)
            tasks = []
            for handler in self.handlers:
                # Check handler level
                if handler.level == LogLevel.NOTSET or level.value >= handler.level.value:
                    if hasattr(handler, 'async_emit'):
                        tasks.append(handler.async_emit(formatted_message, level))
                    else:
                        tasks.append(asyncio.to_thread(handler.emit, formatted_message, level))
            
            await asyncio.gather(*tasks)

    def _sync_log(self, level: LogLevel, message: str, **kwargs):
        # Log everything if level is NOTSET
        if self.level == LogLevel.NOTSET or level.value >= self.level.value:
            formatted_message = self._format_message(level, message, **kwargs)
            for handler in self.handlers:
                # Check handler level
                if handler.level == LogLevel.NOTSET or level.value >= handler.level.value:
                    handler.emit(formatted_message, level)

    def log(self, level: LogLevel, message: str, **kwargs):
        if self.async_mode:
            # Fix: Ensure we're in an async context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.create_task(self._async_log(level, message, **kwargs))
            else:
                return loop.run_until_complete(self._async_log(level, message, **kwargs))
        return self._sync_log(level, message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self.log(LogLevel.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log an exception with traceback."""
        kwargs["exc_info"] = True
        self.error(message, **kwargs)

    def set_context(self, **kwargs):
        self._context_data.update(kwargs)

    def clear_context(self):
        self._context_data.clear()

    def set_style(self, style: str):
        """Set logger style format."""
        if style in LogFormat.TEMPLATES:
            self.format = LogFormat.TEMPLATES[style]
        else:
            raise ValueError(f"Unknown style: {style}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error(f"Context exited with error: {exc_val}")
            return False
        return True
