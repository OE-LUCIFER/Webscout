import os
import time
from datetime import datetime
from pathlib import Path
from typing import Union
from ..core.level import LogLevel

class FileHandler:
    """Handler for outputting log messages to a file with optional rotation."""
    
    def __init__(
        self,
        filename: Union[str, Path],
        mode: str = "a",
        encoding: str = "utf-8",
        level: LogLevel = LogLevel.DEBUG,
        max_bytes: int = 0,
        backup_count: int = 0,
        rotate_on_time: bool = False,
        time_interval: str = "D"  # D=daily, H=hourly, M=monthly
    ):
        """
        Initialize file handler with rotation options.
        
        Args:
            filename: Log file path
            mode: File open mode ('a' for append, 'w' for write)
            encoding: File encoding
            level: Minimum log level to output
            max_bytes: Max file size before rotation (0 = no size limit)
            backup_count: Number of backup files to keep (0 = no backups)
            rotate_on_time: Enable time-based rotation
            time_interval: Rotation interval ('D'=daily, 'H'=hourly, 'M'=monthly)
        """
        self.filename = Path(filename)
        self.mode = mode
        self.encoding = encoding
        self.level = level
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.rotate_on_time = rotate_on_time
        self.time_interval = time_interval.upper()
        
        if self.time_interval not in ["D", "H", "M"]:
            raise ValueError("time_interval must be 'D', 'H', or 'M'")
            
        self._file = None
        self._current_size = 0
        self._last_rollover_time = time.time()
        
        # Create directory if it doesn't exist
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        
        # Open the file
        self._open()
        
    def _open(self):
        """Open or reopen the log file."""
        if self._file:
            self._file.close()
        
        self._file = open(
            self.filename,
            mode=self.mode,
            encoding=self.encoding
        )
        
        self._current_size = self._file.tell()
        if self.mode == "a":
            self._current_size = self.filename.stat().st_size
            
    def _should_rollover(self) -> bool:
        """Check if file should be rolled over based on size or time."""
        if self.max_bytes > 0 and self._current_size >= self.max_bytes:
            return True
            
        if self.rotate_on_time:
            current_time = time.time()
            if self.time_interval == "H":
                interval = 3600  # 1 hour
            elif self.time_interval == "D":
                interval = 86400  # 1 day
            else:  # Monthly
                now = datetime.now()
                if now.month == datetime.fromtimestamp(self._last_rollover_time).month:
                    return False
                return True
                
            if current_time - self._last_rollover_time >= interval:
                return True
                
        return False
        
    def _do_rollover(self):
        """Perform log file rotation."""
        if self._file:
            self._file.close()
            self._file = None
            
        if self.backup_count > 0:
            # Shift existing backup files
            for i in range(self.backup_count - 1, 0, -1):
                sfn = f"{self.filename}.{i}"
                dfn = f"{self.filename}.{i + 1}"
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
                    
            dfn = f"{self.filename}.1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.filename, dfn)
            
        self._open()
        self._last_rollover_time = time.time()
        
    def emit(self, message: str, level: LogLevel):
        """Write log message to file if level is sufficient."""
        if level.value >= self.level.value:
            try:
                if self._should_rollover():
                    self._do_rollover()
                    
                self._file.write(message + "\n")
                self._file.flush()
                self._current_size = self._file.tell()
                
            except Exception as e:
                # Fallback to console on error
                import sys
                sys.stderr.write(f"Error in FileHandler: {e}\n")
                sys.stderr.write(message + "\n")
                
    async def async_emit(self, message: str, level: LogLevel):
        """Asynchronously write log message to file."""
        self.emit(message, level)
        
    def close(self):
        """Close the log file."""
        if self._file:
            self._file.close()
            self._file = None
