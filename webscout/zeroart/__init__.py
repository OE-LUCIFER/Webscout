"""
ZeroArt: A zero-dependency ASCII art text generator

Create awesome ASCII art text without external dependencies!
"""

from .base import ZeroArtFont
from .fonts import BlockFont, SlantFont, NeonFont, CyberFont
from .effects import AsciiArtEffects

def figlet_format(text, font='block'):
    """
    Generate ASCII art text
    
    :param text: Text to convert
    :param font: Font style (default: 'block')
    :return: ASCII art representation of text
    """
    font_map = {
        'block': BlockFont(),
        'slant': SlantFont(),
        'neon': NeonFont(),
        'cyber': CyberFont()
    }
    
    selected_font = font_map.get(font.lower(), BlockFont())
    return selected_font.render(text)

def print_figlet(text, font='block'):
    """
    Print ASCII art text directly
    
    :param text: Text to convert and print
    :param font: Font style (default: 'block')
    """
    print(figlet_format(text, font))

# Expose additional effects
rainbow = AsciiArtEffects.rainbow_effect
glitch = AsciiArtEffects.glitch_effect
wrap_text = AsciiArtEffects.wrap_text
outline = AsciiArtEffects.outline_effect

__all__ = [
    'figlet_format', 
    'print_figlet', 
    'rainbow', 
    'glitch', 
    'wrap_text', 
    'outline',
    'BlockFont', 
    'SlantFont', 
    'NeonFont', 
    'CyberFont'
]