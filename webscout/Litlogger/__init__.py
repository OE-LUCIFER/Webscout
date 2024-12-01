import os
import sys
import json
import threading
import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple

class TextStyle:
    """Text styling options"""
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"
    STRIKE = "\033[9m"
    DOUBLE_UNDERLINE = "\033[21m"
    OVERLINE = "\033[53m"
    RESET = "\033[0m"

class LogFormat:
    """Pre-defined log formats with beautiful styling
    
    Examples:
    >>> logger = LitLogger(format=LogFormat.MODERN_EMOJI)
    >>> logger.info("Server started")  # [2024-01-20 15:30:45] Server started
    
    >>> logger = LitLogger(format=LogFormat.RAINBOW_BOX)
    >>> logger.warning("High CPU")  # Shows warning in a rainbow-colored box
    """
    
    # Basic Formats
    MINIMAL = "[{time}] {level} {message}"
    STANDARD = "[{time}] {level} {name}: {message}"
    DETAILED = "[{time}] {level} {name} [{file}:{line}] >>> {message}"
    
    # Modern Styles
    MODERN = " {time} | {level} | {name} | {message}"
    MODERN_EMOJI = "{emoji} [{time}] {level} {message}"
    MODERN_CLEAN = "{time} {level} {message}"
    MODERN_BRACKET = "【{time}】「{level}」{message}"
    
    # Boxed Styles
    BOXED = """
╭─────────────────────╮
│ [{time}]
│ {level} - {name}
│ {message}
╰─────────────────────╯"""

    DOUBLE_BOX = """
╔══════════════════════╗
║ {level} @ {time}
║ {name}
║ {message}
╚══════════════════════╝"""

    ROUNDED_BOX = """
╭──────────────────────╮
│ {time} • {level}
├──────────────────────┤
│ {message}
╰──────────────────────╯"""

    RAINBOW_BOX = """
 {level} - {time}
  {name}: {message}
"""

    # Debug & Development
    DEBUG = "[{time}] {level} {name} ({file}:{line}) {message}"
    DEBUG_FULL = """
┌─ Debug Info ─┐
│ Time: {time}
│ Level: {level}
│ Name: {name}
│ File: {file}:{line}
│ Message: {message}
└──────────────┘"""

    TRACE = """
 Trace Details:
   Time: {time}
   Level: {level}
   Location: {file}:{line}
   Message: {message}"""

    # Error Formats
    ERROR = "!!! {level} !!! [{time}] {name} - {message}"
    ERROR_DETAILED = """
 {level} ALERT 
Time: {time}
Component: {name}
Location: {file}:{line}
Message: {message}"""

    ERROR_COMPACT = " [{time}] {level}: {message}"
    
    # Status & Progress
    STATUS = """
Status Update:
 Time: {time}
 Level: {level}
 Component: {name}
 Message: {message}"""

    PROGRESS = """
[{time}] Progress Report
├─ Level: {level}
├─ Component: {name}
└─ Status: {message}"""

    # Network & API
    HTTP = """
API {level} [{time}]
Endpoint: {name}
Response: {message}"""

    REQUEST = """
→ Incoming Request
  Time: {time}
  Level: {level}
  API: {name}
  Details: {message}"""

    RESPONSE = """
← Outgoing Response
  Time: {time}
  Level: {level}
  API: {name}
  Details: {message}"""

    # System & Metrics
    SYSTEM = """
 System Event
 {time}
 {level}
 {name}
 {message}"""

    METRIC = """
 Metric Report [{time}]
Level: {level}
Source: {name}
Value: {message}"""

    # Security & Audit
    SECURITY = """
 Security Event 
Time: {time}
Level: {level}
Source: {name}
Event: {message}"""

    AUDIT = """
 Audit Log Entry
Time: {time}
Level: {level}
Component: {name}
Action: {message}"""

    # Special Formats
    RAINBOW = " {time}  {level}  {message}"
    MINIMAL_EMOJI = "{emoji} {message}"
    TIMESTAMP = "{time} {message}"
    COMPONENT = "[{name}] {message}"
    
    # JSON Format (for machine parsing)
    JSON = '{{"time":"{time}","level":"{level}","name":"{name}","message":"{message}"}}'
    
    # XML Format
    XML = """<log>
  <time>{time}</time>
  <level>{level}</level>
  <name>{name}</name>
  <message>{message}</message>
</log>"""

    # Markdown Format
    MARKDOWN = """
## Log Entry
- **Time:** {time}
- **Level:** {level}
- **Component:** {name}
- **Message:** {message}
"""

class ColorScheme:
    """Pre-defined color schemes with rich, carefully crafted color palettes
    
    Examples:
    >>> logger = LitLogger(color_scheme=ColorScheme.CYBERPUNK)
    >>> logger.info("Neon city lights...")
    >>> 
    >>> logger = LitLogger(color_scheme=ColorScheme.AURORA)
    >>> logger.warning("Northern lights warning")
    """
    
    # Cyberpunk theme with neon colors
    CYBERPUNK = {
        "trace": (128, 128, 255),  # Neon blue
        "debug": (255, 0, 255),    # Hot pink
        "info": (0, 255, 255),     # Cyan
        "success": (0, 255, 128),  # Neon green
        "warning": (255, 128, 0),  # Neon orange
        "error": (255, 0, 128),    # Magenta
        "critical": (255, 0, 0)    # Bright red
    }
    
    # Matrix-inspired green theme
    MATRIX = {
        "trace": (0, 100, 0),      # Dark green
        "debug": (0, 150, 0),      # Medium green
        "info": (0, 200, 0),       # Bright green
        "success": (0, 255, 0),    # Pure green
        "warning": (200, 255, 0),  # Yellow-green
        "error": (255, 200, 0),    # Orange-green
        "critical": (255, 0, 0)    # Red alert
    }
    
    # Ocean depths theme
    OCEAN = {
        "trace": (70, 130, 180),   # Steel blue
        "debug": (100, 149, 237),  # Cornflower blue
        "info": (0, 191, 255),     # Deep sky blue
        "success": (127, 255, 212),# Aquamarine
        "warning": (255, 215, 0),  # Gold
        "error": (255, 69, 0),     # Red-orange
        "critical": (255, 0, 0)    # Pure red
    }
    
    # Aurora borealis inspired
    AURORA = {
        "trace": (80, 200, 120),   # Soft green
        "debug": (45, 149, 237),   # Arctic blue
        "info": (148, 87, 235),    # Purple aurora
        "success": (0, 255, 170),  # Northern lights
        "warning": (255, 128, 255),# Pink aurora
        "error": (255, 70, 120),   # Rose red
        "critical": (255, 0, 80)   # Deep pink
    }
    
    # Sunset gradient
    SUNSET = {
        "trace": (255, 155, 0),    # Golden hour
        "debug": (255, 122, 92),   # Coral
        "info": (255, 89, 100),    # Sunset pink
        "success": (255, 166, 0),  # Amber
        "warning": (255, 99, 72),  # Tomato
        "error": (255, 55, 55),    # Sunset red
        "critical": (255, 0, 55)   # Deep sunset
    }
    
    # Retro computing
    RETRO = {
        "trace": (170, 170, 170),  # Light gray
        "debug": (0, 187, 0),      # Phosphor green
        "info": (187, 187, 0),     # Amber
        "success": (0, 255, 0),    # Bright green
        "warning": (255, 187, 0),  # Yellow
        "error": (255, 85, 85),    # Light red
        "critical": (255, 0, 0)    # Bright red
    }
    
    # Pastel dream
    PASTEL = {
        "trace": (173, 216, 230),  # Light blue
        "debug": (221, 160, 221),  # Plum
        "info": (176, 224, 230),   # Powder blue
        "success": (144, 238, 144),# Light green
        "warning": (255, 218, 185),# Peach
        "error": (255, 182, 193),  # Light pink
        "critical": (255, 192, 203)# Pink
    }
    
    # Monochrome elegance
    MONO = {
        "trace": (128, 128, 128),  # Gray
        "debug": (160, 160, 160),  # Light gray
        "info": (192, 192, 192),   # Silver
        "success": (224, 224, 224),# Light silver
        "warning": (96, 96, 96),   # Dark gray
        "error": (64, 64, 64),     # Darker gray
        "critical": (32, 32, 32)   # Almost black
    }
    
    # Forest theme
    FOREST = {
        "trace": (95, 158, 160),   # Cadet blue
        "debug": (85, 107, 47),    # Dark olive
        "info": (34, 139, 34),     # Forest green
        "success": (50, 205, 50),  # Lime green
        "warning": (218, 165, 32), # Golden rod
        "error": (178, 34, 34),    # Firebrick
        "critical": (139, 0, 0)    # Dark red
    }
    
    # Deep space
    SPACE = {
        "trace": (25, 25, 112),    # Midnight blue
        "debug": (72, 61, 139),    # Dark slate blue
        "info": (138, 43, 226),    # Blue violet
        "success": (65, 105, 225), # Royal blue
        "warning": (255, 215, 0),  # Gold
        "error": (220, 20, 60),    # Crimson
        "critical": (178, 34, 34)  # Firebrick
    }

class LogLevel(Enum):
    """Log levels with their string representations and ANSI colors"""
    TRACE = ("TRACE", "trace")
    DEBUG = ("DEBUG", "debug")
    INFO = ("INFO", "info")
    SUCCESS = ("SUCCESS", "success")
    WARNING = ("WARNING", "warning")
    ERROR = ("ERROR", "error")
    CRITICAL = ("CRITICAL", "critical")

    def __init__(self, name: str, color_key: str):
        self._name = name
        self._color_key = color_key

    def __str__(self) -> str:
        return f"[{self._name}]"

    def style(self, style: str, color_scheme: Dict[str, Tuple[int, int, int]]) -> str:
        """Apply a text style and color to the log level"""
        color = color_scheme.get(self._color_key, (255, 255, 255))
        style_code = getattr(TextStyle, style.upper(), "")
        return f"{style_code}\033[38;2;{color[0]};{color[1]};{color[2]}m{str(self)}\033[0m"

    def __ge__(self, other):
        if not isinstance(other, LogLevel):
            return NotImplemented
        levels = list(LogLevel)
        return levels.index(self) >= levels.index(other)

class LitLogger:
    """A lightweight, colorful logger with style and intelligent level detection
    
    Examples:
    >>> logger = LitLogger()
    >>> logger.auto("Starting application...")  # INFO
    >>> logger.auto("CPU: 95%, Memory: 87%")  # WARNING (detected high metrics)
    >>> logger.auto("404: Page not found")  # ERROR (detected status code)
    >>> logger.auto("x = 42, y = [1,2,3]")  # DEBUG (detected variable assignment)
    """
    
    # Enhanced level indicators with weighted patterns
    LEVEL_INDICATORS = {
        LogLevel.ERROR: {
            "patterns": [
                "error", "exception", "failed", "failure", "critical", "fatal",
                "crash", "abort", "terminated", "denied", "invalid", "unauthorized",
                "forbidden", "timeout", "unavailable", "offline", "dead", "killed",
                r"\b(4[0-9]{2}|5[0-9]{2})\b",  # HTTP error codes
                r"err\d+", r"error\d+",         # Error codes
                r"exception\[\d+\]",            # Exception references
                "null pointer", "undefined", "not found", "missing",
                "corruption", "corrupted", "damage", "damaged",
                "exploit", "vulnerability", "breach", "attack",
                "overflow", "underflow", "deadlock", "race condition"
            ],
            "weight": 2.0
        },
        LogLevel.WARNING: {
            "patterns": [
                "warning", "warn", "caution", "alert", "attention",
                "notice", "reminder", "consider", "potential", "possible",
                "deprecated", "unstable", "experimental", "beta",
                "high", "heavy", "excessive", "threshold", "limit",
                "slow", "delayed", "latency", "lag", "bottleneck",
                "suspicious", "unusual", "unexpected", "irregular",
                "restricted", "limited", "constrained", "reaching",
                r"\b8[5-9]%|\b9[0-9]%|100%",    # High percentages
                r"running low", "almost full", "nearing",
                "obsolete", "legacy", "old version", "outdated"
            ],
            "weight": 1.5
        },
        LogLevel.SUCCESS: {
            "patterns": [
                "success", "succeeded", "completed", "done", "ok", "okay",
                "passed", "validated", "verified", "confirmed", "approved",
                "established", "connected", "synchronized", "ready",
                "online", "active", "alive", "running", "operational",
                "deployed", "published", "delivered", "achieved",
                "fixed", "resolved", "solved", "handled", "processed",
                r"2[0-9]{2}",  # HTTP success codes
                "created", "updated", "modified", "changed", "saved"
            ],
            "weight": 1.0
        },
        LogLevel.DEBUG: {
            "patterns": [
                "debug", "debugging", "trace", "tracing", "verbose",
                r"var\s+\w+", r"\w+\s*=\s*[\w\[\{\(]",  # Variable assignments
                r"checking", "testing", "inspecting", "examining",
                "value", "variable", "object", "instance", "type",
                "print", "dump", "output", "log", "console",
                "step", "phase", "stage", "point", "checkpoint",
                r"[\w\.]+\(.*\)",  # Function calls
                "returned", "received", "got", "fetched", "loaded",
                "params", "args", "arguments", "inputs", "outputs"
            ],
            "weight": 0.8
        },
        LogLevel.TRACE: {
            "patterns": [
                "trace", "step", "entering", "exiting", "called",
                "begin", "end", "start", "finish", "init",
                "enter", "exit", "entry", "return", "returns",
                "calling", "called", "invoke", "invoked",
                "request", "response", "sending", "receiving",
                "open", "close", "opened", "closed",
                "load", "unload", "loaded", "unloaded",
                "initialize", "initialized", "setup", "cleanup"
            ],
            "weight": 0.5
        }
    }

    # Metric thresholds for numerical values
    METRIC_THRESHOLDS = {
        "critical": {
            "patterns": ["cpu", "memory", "ram", "disk", "storage", "load", "usage", "utilization", "error_rate", "failure_rate"],
            "threshold": 95,
            "level": LogLevel.ERROR
        },
        "warning": {
            "patterns": ["cpu", "memory", "ram", "disk", "storage", "load", "usage", "utilization", "error_rate", "failure_rate"],
            "threshold": 80,
            "level": LogLevel.WARNING
        },
        "performance": {
            "patterns": ["latency", "delay", "response", "time", "duration", "timeout"],
            "threshold": 1000,  # milliseconds
            "level": LogLevel.WARNING
        }
    }

    def __init__(self, 
                 name: str = "LitLogger",
                 log_path: Optional[Union[str, Path]] = None,
                 console_output: bool = True,
                 time_format: str = "%Y-%m-%d %H:%M:%S",
                 level: Optional[str] = None,
                 format: str = LogFormat.DETAILED,
                 color_scheme: Dict[str, Tuple[int, int, int]] = ColorScheme.OCEAN,
                 level_styles: Optional[Dict[str, str]] = None):
        """Initialize the logger
        
        Examples:
        >>> # Basic console logger
        >>> logger = LitLogger()
        >>> 
        >>> # Customized logger
        >>> logger = LitLogger(
        ...     name="MyApp",
        ...     format=LogFormat.MODERN,
        ...     color_scheme=ColorScheme.NEON
        ... )
        """
        self.name = name
        self.console_output = console_output
        self.time_format = time_format
        self.format = format
        self.color_scheme = color_scheme
        self.level_styles = level_styles or {
            "TRACE": "DIM",
            "DEBUG": "NORMAL",
            "INFO": "NORMAL",
            "SUCCESS": "BOLD",
            "WARNING": "BOLD",
            "ERROR": "BOLD",
            "CRITICAL": "BOLD"
        }
        
        try:
            self.level = LogLevel[level.upper()] if level else LogLevel.TRACE
        except (KeyError, AttributeError):
            print(f"Invalid log level: {level}. Using TRACE level.")
            self.level = LogLevel.TRACE

        self.log_file = None
        if log_path:
            try:
                self.log_file = Path(log_path)
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Failed to initialize log file at {log_path}: {e}")

    def _format_message(self, level: LogLevel, message: str, **kwargs) -> str:
        """Format the log message"""
        # Get caller info
        frame = sys._getframe(2)
        filename = os.path.basename(frame.f_code.co_filename)
        line = frame.f_lineno
        
        # Format time
        time_str = datetime.datetime.now().strftime(self.time_format)
        
        # Format parameters
        params = {
            'time': time_str,
            'level': level.style(self.level_styles.get(level._name, "NORMAL"), self.color_scheme),
            'name': self.name,
            'message': message,
            'file': filename,
            'line': line
        }
        
        try:
            return self.format.format(**params)
        except Exception:
            # Fallback to minimal format
            return f"[{time_str}] {level.style('NORMAL', self.color_scheme)} {message}"

    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        """Log a message"""
        if level >= self.level:
            formatted = self._format_message(level, message, **kwargs)
            
            # Console output
            if self.console_output:
                print(formatted, flush=True)
            
            # File output (without ANSI codes)
            if self.log_file:
                clean_msg = f"[{datetime.datetime.now().strftime(self.time_format)}] [{level._name}] {message}"
                if kwargs:
                    clean_msg += f" Context: {json.dumps(kwargs)}"
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(clean_msg + '\n')
                except Exception as e:
                    print(f"Failed to write to log file: {e}", flush=True)

    def _detect_level(self, message: str, **kwargs) -> LogLevel:
        """Intelligently detect the appropriate log level based on content and context
        
        Uses advanced pattern matching, metric analysis, and context weighting to determine
        the most appropriate log level for any given message.
        
        Examples:
        >>> logger = LitLogger()
        >>> logger._detect_level("CPU usage at 96%")  # ERROR (critical resource usage)
        >>> logger._detect_level("Response time: 1500ms")  # WARNING (high latency)
        >>> logger._detect_level("x = calculate(y)")  # DEBUG (code execution)
        >>> logger._detect_level("HTTP 404: Not Found")  # ERROR (status code)
        """
        message_lower = message.lower()
        
        # Combine message with context for full analysis
        context_str = " ".join(f"{k}={v}" for k, v in kwargs.items()).lower()
        full_text = f"{message_lower} {context_str}"
        
        # Initialize score tracking
        level_scores = {level: 0.0 for level in LogLevel}
        
        # Check for numeric metrics
        for metric_type, config in self.METRIC_THRESHOLDS.items():
            for pattern in config["patterns"]:
                if pattern in full_text:
                    # Extract numbers from the text
                    import re
                    numbers = re.findall(r'\d+(?:\.\d+)?', full_text)
                    for num in numbers:
                        try:
                            value = float(num)
                            if value >= config["threshold"]:
                                level_scores[config["level"]] += 2.0
                        except ValueError:
                            continue
        
        # Pattern matching with weights
        for level, config in self.LEVEL_INDICATORS.items():
            weight = config["weight"]
            for pattern in config["patterns"]:
                import re
                if re.search(pattern, full_text, re.IGNORECASE):
                    level_scores[level] += weight
        
        # Context analysis
        if kwargs:
            # Check for error-like status codes
            status = kwargs.get("status") or kwargs.get("code") or kwargs.get("http_status")
            if status:
                try:
                    status = int(status)
                    if status >= 400:
                        level_scores[LogLevel.ERROR] += 2.0
                    elif status >= 300:
                        level_scores[LogLevel.WARNING] += 1.5
                    elif status >= 200:
                        level_scores[LogLevel.SUCCESS] += 1.0
                except (ValueError, TypeError):
                    pass
        
        # Get the level with the highest score
        max_score = max(level_scores.values())
        if max_score > 0:
            return max(level_scores.items(), key=lambda x: x[1])[0]
        
        # Default to INFO if no strong indicators
        return LogLevel.INFO

    def auto(self, message: str, **kwargs) -> None:
        """Automatically log message with the appropriate level based on content
        
        Examples:
        >>> logger = LitLogger()
        >>> logger.auto("Starting application...")  # INFO
        >>> logger.auto("Warning: Memory usage high", memory=85)  # WARNING
        >>> logger.auto("Error: Database connection failed")  # ERROR
        >>> logger.auto("Debug: x = 42", variable="x", value=42)  # DEBUG
        """
        level = self._detect_level(message, **kwargs)
        self._log(level, message, **kwargs)

    def trace(self, message: str, **kwargs) -> None:
        self._log(LogLevel.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log(LogLevel.INFO, message, **kwargs)

    def success(self, message: str, **kwargs) -> None:
        self._log(LogLevel.SUCCESS, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        self._log(LogLevel.CRITICAL, message, **kwargs)

if __name__ == "__main__":
    # Test all color schemes
    message = "Testing color scheme: {}"
    test_name = "ColorTest"
    
    schemes = [
        ("CYBERPUNK", ColorScheme.CYBERPUNK, LogFormat.MODERN),
        ("AURORA", ColorScheme.AURORA, LogFormat.BOXED),
        ("SUNSET", ColorScheme.SUNSET, LogFormat.ERROR),
        ("RETRO", ColorScheme.RETRO, LogFormat.STANDARD),
        ("PASTEL", ColorScheme.PASTEL, LogFormat.MINIMAL),
        ("MONO", ColorScheme.MONO, LogFormat.DEBUG),
        ("FOREST", ColorScheme.FOREST, LogFormat.DETAILED),
        ("SPACE", ColorScheme.SPACE, LogFormat.MODERN)
    ]
    
    for scheme_name, scheme, format in schemes:
        logger = LitLogger(
            name=f"{test_name}_{scheme_name}",
            format=format,
            color_scheme=scheme
        )
        
        print(f"\n=== Testing {scheme_name} Theme ===")
        logger.trace(f"Trace message in {scheme_name}")
        logger.debug(f"Debug message in {scheme_name}")
        logger.info(f"Info message in {scheme_name}")
        logger.success(f"Success message in {scheme_name}")
        logger.warning(f"Warning message in {scheme_name}")
        logger.error(f"Error message in {scheme_name}")
        logger.critical(f"Critical message in {scheme_name}")
        
        # Test auto-detection with current theme
        logger.auto(f"CPU at 96% in {scheme_name}", cpu=96)
        logger.auto(f"Checking variables in {scheme_name}", x=42, y="test")
        logger.auto(f"HTTP 404 in {scheme_name}", status=404)
        print("=" * 40)
