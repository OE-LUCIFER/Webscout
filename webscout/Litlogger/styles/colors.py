# Terminal Color Management System
# Provides extensive ANSI color support with themes, gradients, and animations

from typing import Optional
from ..core.level import LogLevel


class LogColors:
    """
    Comprehensive terminal color and styling system with support for:
    - Basic and bright colors (foreground/background)
    - RGB and 256-color modes
    - Text styles (bold, italic, etc.)
    - Gradients and animations
    - Predefined themes
    """
    # Reset
    RESET = "\033[0m"
    
    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Bright background colors
    BG_BRIGHT_BLACK = "\033[100m"
    BG_BRIGHT_RED = "\033[101m"
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"
    
    # Custom theme colors using RGB
    FIRE = "\033[38;2;255;100;0m"  # Orange-red
    ICE = "\033[38;2;150;230;255m"  # Light blue
    GRASS = "\033[38;2;120;200;80m"  # Light green
    PURPLE = "\033[38;2;147;112;219m"  # Medium purple
    GOLD = "\033[38;2;255;215;0m"  # Golden
    
    # Gradient colors
    SUNSET_START = "\033[38;2;255;128;0m"  # Orange
    SUNSET_END = "\033[38;2;255;51;153m"  # Pink
    
    OCEAN_START = "\033[38;2;0;204;255m"  # Light blue
    OCEAN_END = "\033[38;2;0;51;102m"  # Dark blue
    
    FOREST_START = "\033[38;2;34;139;34m"  # Forest green
    FOREST_END = "\033[38;2;0;100;0m"  # Dark green
    
    # Bold
    BOLD = "\033[1m"
    
    # Styles
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Level color mapping
    LEVEL_COLORS = {
        LogLevel.DEBUG: BRIGHT_BLACK,
        LogLevel.INFO: BRIGHT_BLUE,
        LogLevel.WARNING: BRIGHT_YELLOW,
        LogLevel.ERROR: BRIGHT_RED,
        LogLevel.CRITICAL: BRIGHT_RED + BOLD,
        LogLevel.NOTSET: WHITE
    }

    # Add style combinations
    STYLES = {
        "bold": "\033[1m",
        "dim": "\033[2m",
        "italic": "\033[3m",
        "underline": "\033[4m",
        "blink": "\033[5m",
        "reverse": "\033[7m",
        "hidden": "\033[8m",
        "strike": "\033[9m",
    }

    @staticmethod
    def rgb(r: int, g: int, b: int, background: bool = False) -> str:
        """Create RGB color code."""
        if background:
            return f"\033[48;2;{r};{g};{b}m"
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def color_256(code: int, background: bool = False) -> str:
        """Create 256-color code."""
        if background:
            return f"\033[48;5;{code}m"
        return f"\033[38;5;{code}m"

    @staticmethod
    def combine(*colors):
        return "".join(colors)

    @staticmethod
    def gradient(text: str, start_rgb: tuple, end_rgb: tuple) -> str:
        """Create a gradient effect across text."""
        if len(text) < 2:
            return LogColors.rgb(*start_rgb) + text
            
        result = []
        for i, char in enumerate(text):
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * i / (len(text) - 1))
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * i / (len(text) - 1))
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * i / (len(text) - 1))
            result.append(f"{LogColors.rgb(r, g, b)}{char}")
            
        return "".join(result) + LogColors.RESET

    @staticmethod
    def rainbow(text: str) -> str:
        """Apply rainbow colors to text."""
        colors = [
            (255, 0, 0),    # Red
            (255, 127, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (75, 0, 130),   # Indigo
            (148, 0, 211)   # Violet
        ]
        
        result = []
        for i, char in enumerate(text):
            color = colors[i % len(colors)]
            result.append(f"{LogColors.rgb(*color)}{char}")
            
        return "".join(result) + LogColors.RESET

    @staticmethod
    def animate(text: str, effect: str = "blink") -> str:
        """Apply animation effects to text."""
        effects = {
            "blink": LogColors.BLINK,
            "reverse": LogColors.REVERSE,
            "bold_blink": LogColors.combine(LogColors.BOLD, LogColors.BLINK),
            "frame_blink": LogColors.combine(LogColors.FRAME, LogColors.BLINK),
            "encircle_blink": LogColors.combine(LogColors.ENCIRCLE, LogColors.BLINK)
        }
        return effects.get(effect, LogColors.BLINK) + text + LogColors.RESET

    @staticmethod
    def style_text(text: str, *styles: str, color: Optional[str] = None) -> str:
        """Apply multiple styles and color to text."""
        style_codes = "".join(LogColors.STYLES.get(style, "") for style in styles)
        color_code = color if color else ""
        return f"{style_codes}{color_code}{text}{LogColors.RESET}"

    @staticmethod
    def level_style(level: LogLevel, text: str) -> str:
        """Style text according to log level with enhanced formatting."""
        color = LogColors.LEVEL_COLORS.get(level, LogColors.RESET)
        
        # Apply appropriate styling based on level
        if level == LogLevel.CRITICAL:
            return f"{color}{LogColors.STYLES['bold']}{text}{LogColors.RESET}"
        elif level == LogLevel.ERROR:
            return f"{color}{text}{LogColors.RESET}"
        elif level == LogLevel.WARNING:
            return f"{color}{text}{LogColors.RESET}"
        else:
            return f"{color}{text}{LogColors.RESET}"


class LogTheme:
    """Pre-defined color themes and combinations."""
    
    @staticmethod
    def get_theme(name: str) -> str:
        themes = {
            # Status themes
            "success": LogColors.combine(LogColors.BRIGHT_GREEN, LogColors.BOLD),
            "error": LogColors.combine(LogColors.BRIGHT_RED, LogColors.BOLD),
            "warning": LogColors.combine(LogColors.BRIGHT_YELLOW, LogColors.BOLD),
            "info": LogColors.combine(LogColors.BRIGHT_BLUE, LogColors.BOLD),
            "debug": LogColors.combine(LogColors.DIM, LogColors.WHITE),
            "critical": LogColors.combine(LogColors.BG_RED, LogColors.WHITE, LogColors.BOLD),
            
            # Special themes
            "header": LogColors.combine(LogColors.BRIGHT_WHITE, LogColors.BOLD, LogColors.UNDERLINE),
            "highlight": LogColors.combine(LogColors.BLACK, LogColors.BG_BRIGHT_YELLOW),
            "important": LogColors.combine(LogColors.BRIGHT_RED, LogColors.BOLD, LogColors.UNDERLINE),
            "subtle": LogColors.combine(LogColors.DIM, LogColors.BRIGHT_BLACK),
            
            # UI themes
            "title": LogColors.combine(LogColors.BRIGHT_WHITE, LogColors.BOLD, LogColors.UNDERLINE),
            "subtitle": LogColors.combine(LogColors.BRIGHT_WHITE, LogColors.DIM),
            "link": LogColors.combine(LogColors.BLUE, LogColors.UNDERLINE),
            "code": LogColors.combine(LogColors.BRIGHT_BLACK, LogColors.BG_WHITE),
            
            # Data themes
            "number": LogColors.combine(LogColors.BRIGHT_CYAN, LogColors.BOLD),
            "string": LogColors.combine(LogColors.BRIGHT_GREEN),
            "boolean": LogColors.combine(LogColors.BRIGHT_YELLOW, LogColors.BOLD),
            "null": LogColors.combine(LogColors.DIM, LogColors.ITALIC),
            
            # Custom themes
            "fire": LogColors.combine(LogColors.FIRE, LogColors.BOLD),
            "ice": LogColors.combine(LogColors.ICE, LogColors.BOLD),
            "nature": LogColors.combine(LogColors.GRASS, LogColors.BOLD),
            "royal": LogColors.combine(LogColors.PURPLE, LogColors.BOLD),
            "precious": LogColors.combine(LogColors.GOLD, LogColors.BOLD),
            
            # Gradient themes
            "sunset": LogColors.combine(LogColors.SUNSET_START, LogColors.SUNSET_END),
            "ocean": LogColors.combine(LogColors.OCEAN_START, LogColors.OCEAN_END),
            "forest": LogColors.combine(LogColors.FOREST_START, LogColors.FOREST_END),
        }
        return themes.get(name, LogColors.RESET)


# Define level colors after both classes are defined
LogColors.LEVEL_COLORS = {
    "DEBUG": LogTheme.get_theme("debug"),
    "INFO": LogTheme.get_theme("info"),
    "WARNING": LogTheme.get_theme("warning"),
    "ERROR": LogTheme.get_theme("error"),
    "CRITICAL": LogTheme.get_theme("critical")
}
