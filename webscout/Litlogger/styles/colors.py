class LogColors:
    # Basic foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"

    # Basic background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Bright foreground colors
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

    # Text styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"
    STRIKE = "\033[9m"
    DOUBLE_UNDERLINE = "\033[21m"

    # Special effects
    FRAME = "\033[51m"
    ENCIRCLE = "\033[52m"
    OVERLINE = "\033[53m"

    # Extended color combinations
    FIRE = "\033[38;2;255;100;0m"
    ICE = "\033[38;2;150;230;255m"
    GRASS = "\033[38;2;0;200;0m"
    PURPLE = "\033[38;2;160;32;240m"
    GOLD = "\033[38;2;255;215;0m"
    SILVER = "\033[38;2;192;192;192m"
    BRONZE = "\033[38;2;205;127;50m"
    PINK = "\033[38;2;255;192;203m"
    TEAL = "\033[38;2;0;128;128m"
    ORANGE = "\033[38;2;255;165;0m"
    BROWN = "\033[38;2;165;42;42m"
    MAROON = "\033[38;2;128;0;0m"
    NAVY = "\033[38;2;0;0;128m"
    OLIVE = "\033[38;2;128;128;0m"

    # Gradient colors
    SUNSET_START = "\033[38;2;255;128;0m"
    SUNSET_END = "\033[38;2;255;0;128m"
    OCEAN_START = "\033[38;2;0;255;255m"
    OCEAN_END = "\033[38;2;0;0;255m"
    FOREST_START = "\033[38;2;34;139;34m"
    FOREST_END = "\033[38;2;0;100;0m"

    # Special background combinations
    BG_FIRE = "\033[48;2;255;100;0m"
    BG_ICE = "\033[48;2;150;230;255m"
    BG_GRASS = "\033[48;2;0;200;0m"
    BG_PURPLE = "\033[48;2;160;32;240m"
    BG_GOLD = "\033[48;2;255;215;0m"
    BG_SILVER = "\033[48;2;192;192;192m"
    BG_BRONZE = "\033[48;2;205;127;50m"
    BG_PINK = "\033[48;2;255;192;203m"
    BG_TEAL = "\033[48;2;0;128;128m"
    BG_ORANGE = "\033[48;2;255;165;0m"
    BG_BROWN = "\033[48;2;165;42;42m"
    BG_MAROON = "\033[48;2;128;0;0m"
    BG_NAVY = "\033[48;2;0;0;128m"
    BG_OLIVE = "\033[48;2;128;128;0m"

    # RGB color support (True color)
    @staticmethod
    def rgb(r: int, g: int, b: int, background: bool = False) -> str:
        """Create RGB color code."""
        if background:
            return f"\033[48;2;{r};{g};{b}m"
        return f"\033[38;2;{r};{g};{b}m"

    # 256 color support
    @staticmethod
    def color_256(code: int, background: bool = False) -> str:
        """Create 256-color code."""
        if background:
            return f"\033[48;5;{code}m"
        return f"\033[38;5;{code}m"

    @staticmethod
    def combine(*styles: str) -> str:
        """Combine multiple color and style codes."""
        return "".join(styles)

    class Theme:
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

    # Level-specific color combinations
    LEVEL_COLORS = {
        "DEBUG": Theme.get_theme("debug"),
        "INFO": Theme.get_theme("info"),
        "WARNING": Theme.get_theme("warning"),
        "ERROR": Theme.get_theme("error"),
        "CRITICAL": Theme.get_theme("critical")
    }

    @staticmethod
    def gradient(text: str, start_rgb: tuple, end_rgb: tuple) -> str:
        """Create a gradient effect across text."""
        if len(text) < 2:
            return LogColors.rgb(*start_rgb) + text
            
        result = []
        for i, char in enumerate(text):
            # Calculate color for this character
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
