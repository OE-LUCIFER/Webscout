
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..styles.colors import LogColors
from ..styles.formats import LogFormat
from .level import LogLevel

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
        level: Union[str, LogLevel] = LogLevel.INFO,
        format: str = LogFormat.MODERN,
        handlers: List = None,
        enable_colors: bool = True,
        async_mode: bool = False
    ):
        self.name = name
        self.level = LogLevel.get_level(level) if isinstance(level, str) else level
        self.format = format
        self.handlers = handlers or []
        self.enable_colors = enable_colors
        self.async_mode = async_mode
        self._context_data = {}
        self._metrics = {}

    def _format_message(self, level: LogLevel, message: str, **kwargs) -> str:
        now = datetime.now()
        log_data = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "time": now.strftime("%H:%M:%S"),  # Add time field
            "date": now.strftime("%Y-%m-%d"),  # Add date field
            "level": level.name,
            "name": self.name,
            "message": message,
            "emoji": self.LEVEL_EMOJIS.get(level, ""),
            **self._context_data,
            **kwargs
        }

        if self.format == LogFormat.JSON:
            return json.dumps(log_data)
        
        try:
            formatted = self.format.format(**log_data)
        except KeyError as e:
            # Fallback to a basic format if the specified format fails
            basic_format = "[{time}] {level}: {message}"
            formatted = basic_format.format(**log_data)
        
        if self.enable_colors:
            color = LogColors.LEVEL_COLORS.get(level, LogColors.RESET)
            return f"{color}{formatted}{LogColors.RESET}"
        return formatted

    async def _async_log(self, level: LogLevel, message: str, **kwargs):
        if level.value < self.level.value:
            return

        formatted_message = self._format_message(level, message, **kwargs)
        tasks = []
        for handler in self.handlers:
            if hasattr(handler, 'async_emit'):
                tasks.append(handler.async_emit(formatted_message, level))
            else:
                tasks.append(asyncio.to_thread(handler.emit, formatted_message, level))
        
        await asyncio.gather(*tasks)

    def _sync_log(self, level: LogLevel, message: str, **kwargs):
        if level.value < self.level.value:
            return

        formatted_message = self._format_message(level, message, **kwargs)
        for handler in self.handlers:
            handler.emit(formatted_message, level)

    def log(self, level: LogLevel, message: str, **kwargs):
        if self.async_mode:
            return asyncio.create_task(self._async_log(level, message, **kwargs))
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

    def set_context(self, **kwargs):
        self._context_data.update(kwargs)

    def clear_context(self):
        self._context_data.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error(f"Context exited with error: {exc_val}")
            return False
        return True