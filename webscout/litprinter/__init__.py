"""
Welcome to WebScout's Advanced Console Printer! 

About This Printer:
- A powerful, feature-rich console output manager
- Created by Abhay Koul as part of the WebScout project
- Designed for beautiful, informative, and interactive terminal output

Core Features:
>>> printer.success("Operation completed successfully! ")
>>> printer.warning("Important notice! ")
>>> printer.info("Here's something interesting ")
>>> printer.error("Houston, we have a problem! ")

Special Features:
-  Rich ANSI color support
-  Data visualization tools
-  Progress bars and spinners
-  Code syntax highlighting
-  Markdown rendering
-  JSON pretty printing

For the best experience, use a terminal that supports UTF-8 and ANSI colors.

>>> # Basic Printing with Style
>>> printer.print("Hello World!", color="blue", bold=True)
>>> printer.print("Important Notice", bg_color="yellow", italic=True)

>>> # Layout and Formatting
>>> printer.print("Centered Text", center=True, width=50)
>>> printer.print("Indented Text", indent=4, prefix="→ ")

>>> # Borders and Decorations
>>> printer.print("Special Message", border=True, rounded_corners=True)
>>> printer.print("Alert", border=True, border_color="red", double_border=True)

>>> # Animations
>>> printer.print("Loading...", animate=True, animation_type="typing")
>>> printer.print("Processing", animate=True, animation_speed=0.1)

>>> # Data Visualization
>>> data = {"status": "active", "users": 100}
>>> printer.print(data, as_json=True)  # Pretty JSON
>>> printer.print(data, as_tree=True)  # Tree View

>>> # Code Highlighting
>>> code = '''def greet(): print("Hello!")'''
>>> printer.print(code, as_code=True, language="python")

>>> # Tables
>>> headers = ["Name", "Status"]
>>> rows = [["Server", "Online"]]
>>> printer.print([headers, rows], as_table=True)

>>> # Markdown Support
>>> printer.print("# Title\n- List item", markdown=True)
"""

import sys
import os
import json
import time
import threading
import re
from typing import Any, Optional, TextIO, Union, Sequence, Dict, List
from datetime import datetime
import textwrap
from collections import defaultdict
import shutil
import inspect
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import Terminal256Formatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

# Enable UTF-8 output on Windows
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    sys.stdout.reconfigure(encoding='utf-8')

# Enable ANSI escape sequences for Windows
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

# ANSI Color Codes
class Colors:
    """ANSI color codes for terminal output."""
    # Base colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    GRAY = '\033[90m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKE = '\033[9m'
    HIDDEN = '\033[8m'
    
    # Special
    RESET = '\033[0m'
    CLEAR_SCREEN = '\033[2J'
    CLEAR_LINE = '\033[2K'
    
    # Cursor movement
    UP = '\033[1A'
    DOWN = '\033[1B'
    RIGHT = '\033[1C'
    LEFT = '\033[1D'

class SyntaxTheme:
    """Syntax highlighting theme."""
    KEYWORD = Colors.MAGENTA + Colors.BOLD
    STRING = Colors.GREEN
    NUMBER = Colors.CYAN
    COMMENT = Colors.BRIGHT_BLACK + Colors.ITALIC
    FUNCTION = Colors.BRIGHT_BLUE
    CLASS = Colors.BRIGHT_YELLOW + Colors.BOLD
    OPERATOR = Colors.WHITE
    BRACKET = Colors.WHITE
    VARIABLE = Colors.BRIGHT_WHITE

class MarkdownTheme:
    """Theme for markdown elements."""
    H1 = Colors.BOLD + Colors.BLUE
    H2 = Colors.BOLD + Colors.CYAN
    H3 = Colors.BOLD + Colors.GREEN
    BOLD = Colors.BOLD
    ITALIC = Colors.ITALIC
    CODE = Colors.YELLOW
    LINK = Colors.BLUE + Colors.UNDERLINE
    LIST_BULLET = Colors.CYAN + "•" + Colors.RESET
    QUOTE = Colors.GRAY
    STRIKE = Colors.STRIKE
    TABLE = Colors.GREEN
    TASK = Colors.YELLOW
    DETAILS = Colors.MAGENTA

class ThemeStyles:
    SUCCESS = f"{Colors.GREEN}{Colors.BOLD}"
    ERROR = f"{Colors.RED}{Colors.BOLD}"
    WARNING = f"{Colors.YELLOW}{Colors.BOLD}"
    INFO = f"{Colors.BLUE}{Colors.BOLD}"
    DEBUG = f"{Colors.MAGENTA}"
    CODE = f"{Colors.CYAN}"

class HoverInfo:
    """Hover information for different elements."""
    BANNER = "A fancy banner to make your output pop!"
    SUCCESS = "Something went right! "
    ERROR = "Oops! Something went wrong "
    WARNING = "Heads up! Something needs attention "
    INFO = "Just some helpful info "
    TABLE = "Data organized in rows and columns "
    TREE = "Hierarchical data visualization "
    JSON = "Pretty-printed JSON data "
    CODE = "Syntax-highlighted code block "

class ProgressBar:
    def __init__(self, total: int, width: int = 40, prefix: str = '', suffix: str = ''):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.suffix = suffix
        self.current = 0
        
    def update(self, current: int):
        self.current = current
        filled = int(self.width * current / self.total)
        bar = f"{Colors.GREEN}{'█' * filled}{Colors.RESET}{'░' * (self.width - filled)}"
        percent = f"{Colors.CYAN}{int(100 * current / self.total)}%{Colors.RESET}"
        print(f'\r{self.prefix} |{bar}| {percent} {self.suffix}', end='', flush=True)
        if current >= self.total:
            print()

class Spinner:
    def __init__(self, message: str = ''):
        self.message = message
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.running = False
        self.thread = None
        
    def spin(self):
        while self.running:
            for frame in self.frames:
                if not self.running:
                    break
                print(f'\r{Colors.CYAN}{frame}{Colors.RESET} {self.message}', end='', flush=True)
                time.sleep(0.1)
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        print('\r' + ' ' * (len(self.message) + 2), end='', flush=True)
        print('\r', end='')

class LitPrinter:
    def __init__(self, 
                 file: TextIO = sys.stdout, 
                 theme: Optional[dict] = None, 
                 indent_size: int = 4,
                 buffer_size: int = 1024,
                 syntax_theme: Optional[Dict[str, str]] = None,
                 markdown_theme: Optional[Dict[str, str]] = None):
        self.file = file
        self.indent_size = indent_size
        self.buffer_size = buffer_size
        self._terminal_width = shutil.get_terminal_size().columns
        self._last_line = ""
        self._spinner_active = False
        self._progress_active = False
        
        # Default theme
        self.theme = theme or {
            "str": Colors.WHITE,
            "int": Colors.CYAN,
            "float": Colors.CYAN,
            "bool": Colors.YELLOW,
            "list": Colors.MAGENTA,
            "dict": Colors.BLUE,
            "none": Colors.RED,
            "timestamp": Colors.GREEN,
            "key": Colors.YELLOW,
            "bracket": Colors.BLUE,
            "comma": Colors.WHITE,
            "colon": Colors.WHITE,
            "url": f"{Colors.BLUE}{Colors.UNDERLINE}",
            "number": Colors.CYAN,
            "special": Colors.MAGENTA + Colors.BOLD,
            "error": Colors.RED + Colors.BOLD,
            "warning": Colors.YELLOW + Colors.BOLD,
            "success": Colors.GREEN + Colors.BOLD,
            "info": Colors.BLUE + Colors.BOLD,
        }
        
        self.syntax_theme = syntax_theme or vars(SyntaxTheme)
        self.markdown_theme = markdown_theme or vars(MarkdownTheme)
        
    def _get_terminal_width(self) -> int:
        """Get the terminal width or default to 80."""
        try:
            width = shutil.get_terminal_size().columns
            return width if width > 0 else 80
        except:
            return 80

    def _format_dict(self, d: dict, indent_level: int = 0) -> str:
        """Format dictionary with proper indentation and colors."""
        if not d:
            return f"{self.theme['bracket']}{{}}{Colors.RESET}"

        indent = " " * (self.indent_size * indent_level)
        next_indent = " " * (self.indent_size * (indent_level + 1))
        
        lines = [f"{self.theme['bracket']}{{{Colors.RESET}"]
        
        for i, (key, value) in enumerate(d.items()):
            # Format key with quotes if it's a string
            if isinstance(key, str):
                formatted_key = f"{self.theme['key']}'{key}'{Colors.RESET}"
            else:
                formatted_key = f"{self.theme['key']}{key}{Colors.RESET}"
                
            # Format value based on type
            if isinstance(value, dict):
                formatted_value = self._format_dict(value, indent_level + 1)
            elif isinstance(value, str):
                # Special handling for URLs
                if any(url_prefix in value.lower() for url_prefix in ['http://', 'https://', 'www.']):
                    formatted_value = f"{self.theme['url']}{value}{Colors.RESET}"
                else:
                    # Word wrap long strings
                    if len(value) > 80:
                        wrapped = textwrap.fill(value, width=80, subsequent_indent=next_indent + "    ")
                        formatted_value = f"{self.theme['str']}'{wrapped}'{Colors.RESET}"
                    else:
                        formatted_value = f"{self.theme['str']}'{value}'{Colors.RESET}"
            elif isinstance(value, (int, float)):
                formatted_value = f"{self.theme['number']}{value}{Colors.RESET}"
            elif isinstance(value, bool):
                formatted_value = f"{self.theme['bool']}{value}{Colors.RESET}"
            elif value is None:
                formatted_value = f"{self.theme['none']}None{Colors.RESET}"
            else:
                formatted_value = self._format_value(value)
            
            # Add comma if not last item
            comma = f"{self.theme['comma']},{Colors.RESET}" if i < len(d) - 1 else ""
            
            lines.append(f"{next_indent}{formatted_key}{self.theme['colon']}: {Colors.RESET}{formatted_value}{comma}")
        
        lines.append(f"{indent}{self.theme['bracket']}}}{Colors.RESET}")
        return '\n'.join(lines)

    def _format_sequence(self, seq: Sequence, indent_level: int = 0) -> str:
        """Format sequences (lists, tuples, sets) with proper indentation."""
        if not seq:
            return f"{self.theme['bracket']}[]{Colors.RESET}"

        indent = " " * (self.indent_size * indent_level)
        next_indent = " " * (self.indent_size * (indent_level + 1))
        
        lines = [f"{self.theme['bracket']}[{Colors.RESET}"]
        
        for i, item in enumerate(seq):
            formatted_item = self._format_value(item, indent_level + 1)
            comma = f"{self.theme['comma']},{Colors.RESET}" if i < len(seq) - 1 else ""
            lines.append(f"{next_indent}{formatted_item}{comma}")
        
        lines.append(f"{indent}{self.theme['bracket']}]{Colors.RESET}")
        return '\n'.join(lines)

    def _format_value(self, value: Any, indent_level: int = 0) -> str:
        """Enhanced format for any value with proper indentation and styling."""
        if value is None:
            return f"{self.theme['none']}None{Colors.RESET}"
        
        if isinstance(value, dict):
            return self._format_dict(value, indent_level)
        
        if isinstance(value, (list, tuple, set)):
            return self._format_sequence(value, indent_level)
        
        if isinstance(value, str):
            return str(value)
        
        if isinstance(value, bool):
            return f"{self.theme['bool']}{str(value)}{Colors.RESET}"
        
        if isinstance(value, (int, float)):
            return f"{self.theme['number']}{str(value)}{Colors.RESET}"
        
        if hasattr(value, '__dict__'):
            return self._format_dict(value.__dict__, indent_level)
        
        return str(value)

    def _highlight_code(self, code: str, language: str = "python") -> str:
        """Print code with that extra drip """
        if PYGMENTS_AVAILABLE:
            try:
                lexer = get_lexer_by_name(language)
                formatter = Terminal256Formatter(style='monokai')
                return highlight(code, lexer, formatter)
            except:
                pass
        
        if language != 'python':
            return code

        lines = []
        for line in code.split('\n'):
            if '#' in line:
                code_part, comment_part = line.split('#', 1)
                line = code_part + f"{self.syntax_theme['COMMENT']}#{comment_part}{Colors.RESET}"
            
            line = re.sub(r'(".*?"|\'.*?\')', 
                         f"{self.syntax_theme['STRING']}\\1{Colors.RESET}", line)
            
            line = re.sub(r'\b(\d+)\b', 
                         f"{self.syntax_theme['NUMBER']}\\1{Colors.RESET}", line)
            
            keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try',
                       'except', 'finally', 'with', 'as', 'import', 'from', 'return']
            
            for keyword in keywords:
                line = re.sub(f'\\b{keyword}\\b', 
                            f"{self.syntax_theme['KEYWORD']}{keyword}{Colors.RESET}", line)
            
            lines.append(line)
        
        return '\n'.join(lines)

    def _format_markdown_stream(self, text: str) -> str:
        """Enhanced markdown formatting for streaming mode."""
        # Headers with emoji flair
        text = re.sub(r'^# (.+)$', f"{self.markdown_theme['H1']}🔥 \\1{Colors.RESET}", text, flags=re.M)
        text = re.sub(r'^## (.+)$', f"{self.markdown_theme['H2']}✨ \\1{Colors.RESET}", text, flags=re.M)
        text = re.sub(r'^### (.+)$', f"{self.markdown_theme['H3']}💫 \\1{Colors.RESET}", text, flags=re.M)
        
        # Bold, italic, and combined with multiple styles
        text = re.sub(r'\*\*\*(.+?)\*\*\*', f"{Colors.BOLD}{Colors.ITALIC}\\1{Colors.RESET}", text)
        text = re.sub(r'\*\*(.+?)\*\*', f"{Colors.BOLD}\\1{Colors.RESET}", text)
        text = re.sub(r'\*(.+?)\*', f"{Colors.ITALIC}\\1{Colors.RESET}", text)
        text = re.sub(r'__(.+?)__', f"{Colors.BOLD}\\1{Colors.RESET}", text)
        text = re.sub(r'_(.+?)_', f"{Colors.ITALIC}\\1{Colors.RESET}", text)
        
        # Code blocks and inline code
        text = re.sub(r'```(\w+)?\n(.*?)\n```', lambda m: self._highlight_code(m.group(2), m.group(1) or 'text'), text, flags=re.S)
        text = re.sub(r'`(.+?)`', f"{Colors.CYAN}\\1{Colors.RESET}", text)
        
        # Lists with proper indentation and bullets
        lines = text.split('\n')
        formatted_lines = []
        for i, line in enumerate(lines):
            # Match different bullet point styles
            bullet_match = re.match(r'^(\s*)([-•*]|\d+\.) (.+)$', line)
            if bullet_match:
                indent, bullet, content = bullet_match.groups()
                indent_level = len(indent) // 2
                
                # Choose bullet style based on nesting level
                if indent_level == 0:
                    bullet_style = "•"
                elif indent_level == 1:
                    bullet_style = "◦"
                else:
                    bullet_style = "▪"
                
                # Format the line with proper indentation and bullet
                formatted_line = f"{' ' * (indent_level * 2)}{Colors.CYAN}{bullet_style}{Colors.RESET} {content}"
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)
        text = '\n'.join(formatted_lines)
        
        # Links with underline
        text = re.sub(r'\[(.+?)\]\((.+?)\)', f"{Colors.BLUE}{Colors.UNDERLINE}\\1{Colors.RESET}", text)
        
        # Blockquotes with style
        text = re.sub(r'^> (.+)$', f"{self.markdown_theme['QUOTE']}│ \\1{Colors.RESET}", text, flags=re.M)
        
        # Strikethrough
        text = re.sub(r'~~(.+?)~~', f"{Colors.STRIKE}\\1{Colors.RESET}", text)
        
        # Task lists with fancy checkboxes
        text = re.sub(r'- \[ \] (.+)$', f"{self.markdown_theme['TASK']}☐ \\1{Colors.RESET}", text, flags=re.M)
        text = re.sub(r'- \[x\] (.+)$', f"{self.markdown_theme['TASK']}☑ \\1{Colors.RESET}", text, flags=re.M)
        
        # Tables with borders
        table_pattern = r'\|(.+?)\|[\r\n]+\|[-:| ]+\|[\r\n]+((?:\|.+?\|[\r\n]+)+)'
        text = re.sub(table_pattern, self._format_table_markdown, text, flags=re.M)
        
        return text

    def _format_table_markdown(self, match) -> str:
        """Format markdown tables with style."""
        header = [cell.strip() for cell in match.group(1).split('|') if cell.strip()]
        rows = []
        for row in match.group(2).strip().split('\n'):
            cells = [cell.strip() for cell in row.split('|')[1:-1]]
            if cells:
                rows.append(cells)
        
        # Get column widths
        widths = [max(len(str(row[i])) for row in [header] + rows) for i in range(len(header))]
        
        # Build table
        result = []
        # Header
        result.append('┌' + '┬'.join('─' * (w + 2) for w in widths) + '┐')
        result.append('│ ' + ' │ '.join(f"{h:<{w}}" for h, w in zip(header, widths)) + ' │')
        result.append('├' + '┼'.join('─' * (w + 2) for w in widths) + '┤')
        # Rows
        for row in rows:
            result.append('│ ' + ' │ '.join(f"{str(c):<{w}}" for c, w in zip(row, widths)) + ' │')
        result.append('└' + '┴'.join('─' * (w + 2) for w in widths) + '┘')
        
        return '\n'.join(result)

    def print(self, *args, 
             # Builtin print compatibility
             sep: str = " ",
             end: str = "\n",
             file: Optional[TextIO] = None,
             flush: bool = True,
             
             # Styling options
             style: Optional[str] = None,
             color: Optional[str] = None,
             bg_color: Optional[str] = None,
             bold: bool = False,
             italic: bool = False,
             underline: bool = False,
             blink: bool = False,
             strike: bool = False,
             dim: bool = False,
             reverse: bool = False,
             
             # Layout options
             markdown: Optional[bool] = None,
             highlight: bool = False,
             center: bool = False,
             indent: int = 0,
             prefix: Optional[str] = None,
             suffix: Optional[str] = None,
             width: Optional[int] = None,
             padding: int = 0,
             margin: int = 0,
             align: str = "left",
             
             # Border options
             border: bool = False,
             border_style: Optional[str] = None,
             border_char: str = "─",
             border_color: Optional[str] = None,
             rounded_corners: bool = False,
             double_border: bool = False,
             
             # Animation options
             animate: bool = False,
             animation_speed: float = 0.05,
             animation_type: str = "typing",
             
             # Special features
             as_table: bool = False,
             as_tree: bool = False,
             as_json: bool = False,
             as_code: bool = False,
             language: str = "python",
             
             # Advanced features
             raw: bool = False) -> None:
        """
        Enhanced print with all builtin features plus rich formatting.
        
        Supports all builtin print parameters plus rich formatting features.
        Automatically detects and formats markdown content unless explicitly disabled.
        """
        # Handle raw output mode
        if raw:
            print(*args, sep=sep, end=end, file=file or self.file, flush=flush)
            return
            
        # Join args with separator
        output = sep.join(str(arg) for arg in args)
        
        # Auto-detect markdown if not explicitly set
        if markdown is None:  
            markdown = any(marker in output for marker in [
                '#', '*', '_', '`', '>', '-', '•', '|',  
                # '✨', '🔥', '💫', '☐', '☑',             
                'http://', 'https://',                   
                '```', '~~~',                           
                '<details>', '<summary>',               
            ])
        
        # Apply markdown formatting if enabled
        if markdown:
            output = self._format_markdown_stream(output)
        
        # Build style string
        style_str = style or ""
        if color:
            style_str += getattr(Colors, color.upper(), "")
        if bg_color:
            style_str += getattr(Colors, f"BG_{bg_color.upper()}", "")
        if bold:
            style_str += Colors.BOLD
        if italic:
            style_str += Colors.ITALIC
        if underline:
            style_str += Colors.UNDERLINE
        if blink:
            style_str += Colors.BLINK
        if strike:
            style_str += Colors.STRIKE
        if dim:
            style_str += Colors.DIM
        if reverse:
            style_str += Colors.REVERSE
        
        # Apply style if any
        if style_str:
            output = f"{style_str}{output}{Colors.RESET}"
        
        # Handle special formatting
        if as_json:
            output = self._format_json(output)
        elif as_code:
            output = self._highlight_code(output, language)
        elif as_table:
            if isinstance(output, (list, tuple)):
                self.table(*output)
                return
        elif as_tree:
            if isinstance(output, (dict, list)):
                self.tree(output)
                return
        
        # Apply layout options
        if center:
            term_width = self._get_terminal_width()
            output = output.center(term_width)
        if indent > 0:
            output = " " * (indent * 4) + output
        if prefix:
            output = prefix + output
        if suffix:
            output = output + suffix
        if width:
            output = textwrap.fill(output, width=width)
        
        # Add borders
        if border:
            width = max(len(line) for line in output.split('\n'))
            border_top = '┌' + border_char * width + '┐'
            border_bottom = '└' + border_char * width + '┘'
            output = f"{border_top}\n{output}\n{border_bottom}"
        
        # Handle animation
        if animate:
            for char in output:
                print(char, end="", flush=True)
                time.sleep(animation_speed)
            print(end=end, flush=flush)
            return
        
        # Final output
        print(output, end=end, file=file or self.file, flush=flush)

    def status(self, text: str, style: Optional[str] = None):
        """Print a status message that can be overwritten."""
        style = style or self.theme['info']
        self._clear_line()
        self._last_line = f"{style}{text}{Colors.RESET}"
        print(self._last_line, end='\r', file=self.file, flush=True)

    def banner(self, text: str, style: Optional[str] = None):
        """Print a fancy banner with hover info."""
        print(f"\033]1337;Custom=id=banner:{HoverInfo.BANNER}\a", end='')
        style = style or self.theme['special']
        width = self._get_terminal_width() - 4
        
        lines = textwrap.wrap(text, width=width, break_long_words=False)
        
        print('╔' + '═' * width + '╗')
        for line in lines:
            padding = width - len(line)
            print('║ ' + line + ' ' * padding + ' ║')
        print('╚' + '═' * width + '╝')
        print("\033]1337;Custom=id=banner:end\a", end='')

    def success(self, text: str):
        """Print a success message with hover info."""
        print(f"\033]1337;Custom=id=success:{HoverInfo.SUCCESS}\a", end='')
        self.print(f"✓ {text}", style=self.theme['success'])
        print("\033]1337;Custom=id=success:end\a", end='')

    def error(self, text: str):
        """Print an error message with hover info."""
        print(f"\033]1337;Custom=id=error:{HoverInfo.ERROR}\a", end='')
        self.print(f"✗ {text}", style=self.theme['error'])
        print("\033]1337;Custom=id=error:end\a", end='')

    def warning(self, text: str):
        """Print a warning message with hover info."""
        print(f"\033]1337;Custom=id=warning:{HoverInfo.WARNING}\a", end='')
        self.print(f"⚠ {text}", style=self.theme['warning'])
        print("\033]1337;Custom=id=warning:end\a", end='')

    def info(self, text: str):
        """Print an info message with hover info."""
        print(f"\033]1337;Custom=id=info:{HoverInfo.INFO}\a", end='')
        self.print(f"ℹ {text}", style=self.theme['info'])
        print("\033]1337;Custom=id=info:end\a", end='')

    def table(self, headers: List[str], rows: List[List[Any]], style: Optional[str] = None):
        """Print a formatted table."""
        style = style or self.theme['special']
        
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        header_line = '| ' + ' | '.join(f"{h:<{w}}" for h, w in zip(headers, col_widths)) + ' |'
        print(header_line)

        separator = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'
        print(separator)

        for row in rows:
            row_line = '| ' + ' | '.join(f"{str(cell):<{w}}" for cell, w in zip(row, col_widths)) + ' |'
            print(row_line)

    def tree(self, data: Union[Dict, List], indent: int = 0):
        """Print a tree structure of nested data."""
        if isinstance(data, dict):
            for key, value in data.items():
                self.print("  " * indent + "├─ " + str(key) + ":", style=self.theme['key'])
                if isinstance(value, (dict, list)):
                    self.tree(value, indent + 1)
                else:
                    self.print("  " * (indent + 1) + "└─ " + str(value))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self.tree(item, indent + 1)
                else:
                    self.print("  " * indent + "├─ " + str(item))

    def json(self, data: Any, indent: int = 4):
        """Print formatted JSON data."""
        formatted = json.dumps(data, indent=indent)
        self.print(formatted, highlight=True)

    def code_block(self, code: str, language: str = "python"):
        """Print code in a fancy box with syntax highlighting."""
        highlighted = self._highlight_code(code, language)
        lines = highlighted.split('\n')
        
        width = max(len(line) for line in lines)
        width = min(width, self._get_terminal_width() - 4)  # Account for borders
        
        print('┌' + '─' * width + '┐')
        
        for line in lines:
            if len(line) > width:
                line = line[:width-3] + '...'
            else:
                line = line + ' ' * (width - len(line))
            print('│ ' + line + ' │')
        
        print('└' + '─' * width + '┘')

    def _clear_line(self):
        """Clear the current line."""
        print('\r' + ' ' * self._get_terminal_width(), end='\r', file=self.file, flush=True)

if __name__ == "__main__":
    printer = LitPrinter()
    
    printer.banner("Welcome to the LitPrinter Demo! ")
    
    printer.status("Loading that heat... ")
    time.sleep(1)
    printer.status("Almost ready to drop... ")
    time.sleep(1)
    printer.status("")
    
    printer.success("Ayy, we made it! ")
    printer.error("Houston, we got a problem! ")
    printer.warning("Hold up, something sus... ")
    printer.info("Just so you know fam... ")
    
    headers = ["Name", "Vibe", "Energy"]
    rows = [
        ["Python", "Immaculate", "100%"],
        ["Java", "Decent", "75%"],
        ["C++", "Complex", "85%"]
    ]
    printer.table(headers, rows)
    
    data = {
        "squad": {
            "python": {"vibe": "lit", "power": "over 9000"},
            "javascript": {"vibe": "cool", "power": "8000"}
        },
        "config": {
            "mode": "beast",
            "activated": True
        }
    }
    printer.tree(data)
    
    printer.json(data)
    
    code = '''def print_drip():
    # This function brings the heat 
    print("Straight bussin!")
    return True  # No cap'''
    printer.code_block(code)
    
    printer.print("Basic text but make it  fancy ")
    printer.print("Colors go hard", style=Colors.GREEN)
    printer.print("Bold & Blue = Different breed", style=Colors.BLUE + Colors.BOLD)
    
    markdown_text = """# Main Title (Straight Fire)
## Subtitle (Also Heat)
- First thing's first
- Second thing's second
**Bold moves** and *smooth style*
"""
    printer.print(markdown_text, markdown=True)
    
    test_dict = {
        "name": "LitPrinter",
        "vibes": ["immaculate", "unmatched", "different"],
        "config": {"mode": "beast", "level": "over 9000"}
    }
    printer.print(test_dict)