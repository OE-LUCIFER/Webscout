
import asyncio
import sys
import threading
import traceback
from datetime import datetime
from typing import List, Union

from ..core.level import LogLevel
from ..styles.formats import LogFormat

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
        level: Union[str, LogLevel, None] = None,
        format: Union[str, LogFormat] = LogFormat.MODERN_EMOJI,
        handlers: List = None,
        enable_colors: bool = True,
        async_mode: bool = False,
        show_thread: bool = True,
        show_context: bool = True
    ):
        self.name = name
        self.level = LogLevel.NOTSET if level is None else (
            LogLevel.get_level(level) if isinstance(level, str) else level
        )
        self.format = format
        self.enable_colors = enable_colors
        self.async_mode = async_mode
        self.show_thread = show_thread
        self.show_context = show_context
        self._context_data = {}
        
        # Initialize with default console handler if none provided
        if handlers is None:
            from ..handlers.console import ConsoleHandler
            self.handlers = [ConsoleHandler(level=self.level)]
        else:
            self.handlers = handlers

    def _format_message(self, level: LogLevel, message: str, **kwargs) -> str:
        now = datetime.now()
        emoji = self.LEVEL_EMOJIS.get(level, "") if self.enable_colors else ""
        
        log_data = {
            "timestamp": now.strftime("%H:%M:%S"),
            "level": level.name,
            "name": self.name,
            "message": str(message),
            "emoji": emoji,
            "thread": threading.current_thread().name if self.show_thread else "",
        }
        
        # Add context data
        if self.show_context and self._context_data:
            log_data.update(self._context_data)
        
        # Add extra kwargs
        log_data.update(kwargs)
        
        # Format exception if present
        if 'exc_info' in kwargs:
            exc_info = kwargs['exc_info']
            if exc_info:
                exception_text = ''.join(traceback.format_exception(*exc_info))
                log_data['message'] = f"{message}\n{exception_text}"
        
        try:
            base_message = f"{emoji} [{log_data['timestamp']}] {level.name} {log_data['message']}"
            return base_message
        except Exception as e:
            return f"[{log_data['timestamp']}] {level.name}: {message}"

    def _log(self, level: LogLevel, message: str, **kwargs):
        if self.async_mode:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.create_task(self._async_log(level, message, **kwargs))
            else:
                return loop.run_until_complete(self._async_log(level, message, **kwargs))
        return self._sync_log(level, message, **kwargs)

    def debug(self, message: str, **kwargs):
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(LogLevel.CRITICAL, message, **kwargs)

    def exception(self, message: str, exc_info=True, **kwargs):
        """
        Log an exception with traceback.
        
        Args:
            message: The message to log
            exc_info: If True, adds exception info to the message. Can also be a tuple (type, value, traceback)
            **kwargs: Additional key-value pairs to log
        """
        if exc_info:
            if not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        kwargs['exc_info'] = exc_info
        self.error(message, **kwargs)

    def _sync_log(self, level: LogLevel, message: str, **kwargs):
        if self._should_log(level):
            formatted_message = self._format_message(level, message, **kwargs)
            for handler in self.handlers:
                if handler.level == LogLevel.NOTSET or level.value >= handler.level.value:
                    handler.emit(formatted_message, level)

    async def _async_log(self, level: LogLevel, message: str, **kwargs):
        if self._should_log(level):
            formatted_message = self._format_message(level, message, **kwargs)
            tasks = []
            for handler in self.handlers:
                if handler.level == LogLevel.NOTSET or level.value >= handler.level.value:
                    if hasattr(handler, 'async_emit'):
                        tasks.append(handler.async_emit(formatted_message, level))
                    else:
                        tasks.append(asyncio.to_thread(handler.emit, formatted_message, level))
            await asyncio.gather(*tasks)

    def _should_log(self, level: LogLevel) -> bool:
        return self.level == LogLevel.NOTSET or level.value >= self.level.value

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
