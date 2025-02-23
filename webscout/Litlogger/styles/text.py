import textwrap
from typing import Optional

class TextStyle:
    @staticmethod
    def wrap(text: str, width: int = 80, indent: str = "") -> str:
        """Wrap text to specified width with optional indentation."""
        return textwrap.fill(text, width=width, initial_indent=indent, 
                           subsequent_indent=indent)

    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length with suffix."""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def pad(text: str, width: int, align: str = "left", 
           fill_char: str = " ") -> str:
        """Pad text to specified width with alignment."""
        if align == "left":
            return text.ljust(width, fill_char)
        elif align == "right":
            return text.rjust(width, fill_char)
        elif align == "center":
            return text.center(width, fill_char)
        raise ValueError(f"Invalid alignment: {align}")

    @staticmethod
    def indent(text: str, prefix: str = "  ", predicate: Optional[callable] = None) -> str:
        """Indent text lines with prefix based on optional predicate."""
        lines = text.splitlines(True)
        if predicate is None:
            predicate = bool
        
        def should_indent(line):
            return predicate(line)

        return "".join(prefix + line if should_indent(line) else line
                      for line in lines)

    @staticmethod
    def highlight(text: str, substring: str, color: str) -> str:
        """Highlight substring within text using ANSI color codes."""
        from ..styles.colors import LogColors
        if not substring:
            return text
        
        parts = text.split(substring)
        highlighted = f"{color}{substring}{LogColors.RESET}"
        return highlighted.join(parts)

    @staticmethod
    def table(headers: list, rows: list, padding: int = 1) -> str:
        """Create a formatted table with headers and rows."""
        if not rows:
            return ""
            
        # Calculate column widths
        widths = [max(len(str(row[i])) for row in [headers] + rows)
                 for i in range(len(headers))]
        
        # Create separator line
        separator = "+" + "+".join("-" * (w + 2 * padding) for w in widths) + "+"
        
        # Format header
        header = "|" + "|".join(
            str(h).center(w + 2 * padding) for h, w in zip(headers, widths)
        ) + "|"
        
        # Format rows
        formatted_rows = []
        for row in rows:
            formatted_row = "|" + "|".join(
                str(cell).ljust(w + 2 * padding) for cell, w in zip(row, widths)
            ) + "|"
            formatted_rows.append(formatted_row)
        
        # Combine all parts
        return "\n".join([
            separator,
            header,
            separator,
            *formatted_rows,
            separator
        ])
