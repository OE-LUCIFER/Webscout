
class LogFormat:
    # Basic formats with improved styling
    MINIMAL = "│ {time} │ {level} │ {message}"
    STANDARD = "┌─ {time} ─┐\n│ {level} │ {name}: {message}"
    DETAILED = """╭──────────────────────╮
│ {time}
│ {level} • {name}
│ {file}:{line}
├──────────────────────┤
│ {message}
╰──────────────────────╯"""
    SIMPLE = "• {message}"
    COMPACT = "⟦{time}⟧ {level} ⟫ {message}"
    
    # Modern Styles with Unicode
    MODERN = """┌────────────────────┐
│ {time}
├────────────────────┤
│ {level} • {name}
│ {message}
└────────────────────┘"""
    
    MODERN_EMOJI = """╭─ {emoji} {time} ─╮
│ {level}
├───────────────────
│ {message}
╰───────────────────"""
    
    MODERN_CLEAN = """• {time} •
┌─ {level}
└→ {message}"""
    
    MODERN_BRACKET = """【{time}】
「{level}」{message}"""
    
    MODERN_PLUS = """⊕ {time}
├─ {level}
└─ {message}"""
    
    MODERN_DOT = """● {time}
├● {level}
└● {message}"""
    
    MODERN_ARROW = """➤ {time}
├➤ {level}
└➤ {message}"""
    
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

    HEAVY_BOX = """
┏━━━━━━━━━━━━━━━━━━━━┓
┃ {time}
┃ {level} | {name}
┃ {message}
┗━━━━━━━━━━━━━━━━━━━━┛"""

    DOTTED_BOX = """
╭┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈╮
┊ {time} | {level}
┊ {message}
╰┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈╯"""

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

    DEBUG_COMPACT = "[DBG][{time}] {message} @{file}:{line}"
    DEBUG_EXTENDED = """
🔍 Debug Information 🔍
⏰ Time: {time}
📊 Level: {level}
📂 File: {file}
📍 Line: {line}
💬 Message: {message}
"""

    # Enhanced Error Formats
    ERROR = """╔══ ERROR ══╗
║ Time: {time}
║ Level: {level}
║ Component: {name}
╟──────────────
║ {message}
╚════════════╝"""

    ERROR_DETAILED = """┏━━ ALERT ━━┓
┃ Time: {time}
┃ Level: {level}
┃ Component: {name}
┃ Location: {file}:{line}
┣━━━━━━━━━━━
┃ {message}
┗━━━━━━━━━━━┛"""

    ERROR_COMPACT = "‼ [{time}] {level}: {message}"
    
    ERROR_EMOJI = """❌ ERROR REPORT
⏰ {time}
⚠️ {level}
📝 {message}"""

    ERROR_BLOCK = """█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█  ERROR @ {time}
█  {level}
█  {message}
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█"""

    # Status & Progress with Better Visual Hierarchy
    STATUS = """┌─── Status Update ───┐
│ Time: {time}
│ Level: {level}
│ Component: {name}
├───────────────────┤
│ {message}
└───────────────────┘"""

    PROGRESS = """╭── Progress Report ──╮
│ Time: {time}
│ Level: {level}
├────────────────────
│ Component: {name}
│ Status: {message}
╰────────────────────"""

    PROGRESS_SIMPLE = "► {time} | {level} | {message}"
    PROGRESS_BAR = "[{progress_bar}] {percentage}% - {message}"
    
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

    API_COMPACT = "{method} {url} - {status_code} ({time})"
    API_DETAILED = """┌── API Request ──┐
│ Time: {time}
│ Method: {method}
│ URL: {url}
├─────────────────
│ Status: {status_code}
│ {message}
└─────────────────"""

    # System & Metrics
    SYSTEM = """┌─── System Status ───┐
│ {time}
├───────────────────────
│ Component: {name}
│ Status: {level}
│ Message: {message}
└───────────────────────"""

    METRIC = """┌── Metrics ──┐
│ Time: {time}
│ Value: {value}{units}
│ {message}
└─────────────"""

    METRIC_COMPACT = "[METRIC] {name}={value} {units}"
    METRIC_JSON = '{{"metric":"{name}","value":{value},"time":"{time}"}}'
    
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

    SECURITY_ALERT = """╔═══ SECURITY ALERT ═══╗
║ Time: {time}
║ Level: {level}
║ Component: {name}
╟───────────────────────
║ {message}
╚═══════════════════════"""

    # Special Formats
    RAINBOW = " {time}  {level}  {message}"
    MINIMAL_EMOJI = "{emoji} {message}"
    TIMESTAMP = "{time} {message}"
    COMPONENT = "[{name}] {message}"
    HASH = "#{hash} | {time} | {message}"
    TAG = "@{tag} | {time} | {message}"

    # Data Formats
    JSON = '{{"time":"{time}","level":"{level}","name":"{name}","message":"{message}"}}'
    JSON_PRETTY = """{
    "timestamp": "{time}",
    "level": "{level}",
    "component": "{name}",
    "message": "{message}"
}"""
    
    XML = """<log>
  <time>{time}</time>
  <level>{level}</level>
  <name>{name}</name>
  <message>{message}</message>
</log>"""

    YAML = """---
timestamp: {time}
level: {level}
component: {name}
details:
  message: {message}
"""

    # Modern Documentation Formats
    MARKDOWN = """## Log Entry
**Time:** `{time}`
**Level:** `{level}`
**Component:** `{name}`

> {message}
---"""

    RST = """
Log Entry
=========
:Time: {time}
:Level: {level}
:Component: {name}
:Message: {message}
"""

    HTML = """<div class="log-entry">
    <div class="log-header">
        <span class="time">{time}</span>
        <span class="level">{level}</span>
    </div>
    <div class="log-body">
        <span class="name">{name}</span>
        <span class="message">{message}</span>
    </div>
</div>"""

    # Rich Console Formats
    RICH = """╭── {name} ──╮
│ {time} │ {level_colored}
├──────────┴───────────
│ {message}
│ {context}{exception}
╰────────────────────"""
    
    RICH_DETAILED = """╔══════════════════════════╗
║ {name}                    
╟──────────────────────────
║ Time: {time}
║ Level: {level_colored}
║ Thread: {thread_info}
╟──────────────────────────
║ {message}
║ {context}{exception}
╚══════════════════════════╝"""

    RICH_MINIMAL = "│ {time} │ {level_colored} │ {message}"
    
    RICH_COMPACT = "⟦{time}⟧ {level_colored} [{name}] ⟫ {message}"

    # Template registry
    TEMPLATES = {
        # Basic formats
        "minimal": MINIMAL,
        "standard": STANDARD,
        "detailed": DETAILED,
        "simple": SIMPLE,
        "compact": COMPACT,

        # Modern styles
        "modern": MODERN,
        "modern_emoji": MODERN_EMOJI,
        "modern_clean": MODERN_CLEAN,
        "modern_bracket": MODERN_BRACKET,
        "modern_plus": MODERN_PLUS,
        "modern_dot": MODERN_DOT,
        "modern_arrow": MODERN_ARROW,

        # Boxed styles
        "boxed": BOXED,
        "double_box": DOUBLE_BOX,
        "rounded_box": ROUNDED_BOX,
        "rainbow_box": RAINBOW_BOX,
        "heavy_box": HEAVY_BOX,
        "dotted_box": DOTTED_BOX,

        # Debug formats
        "debug": DEBUG,
        "debug_full": DEBUG_FULL,
        "trace": TRACE,
        "debug_compact": DEBUG_COMPACT,
        "debug_extended": DEBUG_EXTENDED,

        # Error formats
        "error": ERROR,
        "error_detailed": ERROR_DETAILED,
        "error_compact": ERROR_COMPACT,
        "error_emoji": ERROR_EMOJI,
        "error_block": ERROR_BLOCK,

        # Status formats
        "status": STATUS,
        "progress": PROGRESS,
        "progress_simple": PROGRESS_SIMPLE,
        "progress_bar": PROGRESS_BAR,

        # Network formats
        "http": HTTP,
        "request": REQUEST,
        "response": RESPONSE,
        "api_compact": API_COMPACT,
        "api_detailed": API_DETAILED,

        # System formats
        "system": SYSTEM,
        "metric": METRIC,
        "metric_compact": METRIC_COMPACT,
        "metric_json": METRIC_JSON,

        # Security formats
        "security": SECURITY,
        "audit": AUDIT,
        "security_alert": SECURITY_ALERT,

        # Special formats
        "rainbow": RAINBOW,
        "minimal_emoji": MINIMAL_EMOJI,
        "timestamp": TIMESTAMP,
        "component": COMPONENT,
        "hash": HASH,
        "tag": TAG,

        # Data formats
        "json": JSON,
        "json_pretty": JSON_PRETTY,
        "xml": XML,
        "yaml": YAML,

        # Documentation formats
        "markdown": MARKDOWN,
        "rst": RST,
        "html": HTML,

        # Rich-like formats
        "rich": RICH,
        "rich_detailed": RICH_DETAILED,
        "rich_minimal": RICH_MINIMAL,
        "rich_compact": RICH_COMPACT,
    }

    @staticmethod
    def create_custom(template: str) -> str:
        """Create a custom log format template."""
        try:
            # Test if the template is valid by formatting with dummy data
            dummy_data = {
                "time": "2024-01-01 00:00:00",
                "level": "INFO",
                "name": "test",
                "message": "test message",
                "file": "test.py",
                "line": 1,
                "emoji": "✨",
                "progress_bar": "==========",
                "percentage": 100,
                "method": "GET",
                "url": "/test",
                "status_code": 200,
                "value": 42,
                "units": "ms",
                "hash": "abc123",
                "tag": "test"
            }
            template.format(**dummy_data)
            return template
        except KeyError as e:
            raise ValueError(f"Invalid format template. Missing key: {e}")
        except Exception as e:
            raise ValueError(f"Invalid format template: {e}")

    @staticmethod
    def get_format(format_name: str) -> str:
        """Get a predefined format template by name."""
        if format_name in LogFormat.TEMPLATES:
            return LogFormat.TEMPLATES[format_name]
        raise ValueError(f"Unknown format: {format_name}")

    @staticmethod
    def register_template(name: str, template: str):
        """Register a new format template."""
        if name in LogFormat.TEMPLATES:
            raise ValueError(f"Format template '{name}' already exists")
        
        # Validate template before registering
        LogFormat.create_custom(template)
        LogFormat.TEMPLATES[name] = template
