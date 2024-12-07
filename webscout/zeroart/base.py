"""
ZeroArt Base: Core classes and utilities for ASCII art generation
"""

class ZeroArtFont:
    """Base class for ASCII art fonts"""
    def __init__(self, name):
        self.name = name
        self.letters = {}
        self.special_chars = {}

    def add_letter(self, char, art_lines):
        """
        Add a custom letter to the font
        
        :param char: Character to add
        :param art_lines: List of art lines representing the character
        """
        self.letters[char.upper()] = art_lines

    def add_special_char(self, name, art_lines):
        """
        Add a special ASCII art character or design
        
        :param name: Name of the special character
        :param art_lines: List of art lines representing the character
        """
        self.special_chars[name] = art_lines

    def get_letter(self, char):
        """
        Get ASCII art for a specific character
        
        :param char: Character to retrieve
        :return: List of art lines or default space
        """
        return self.letters.get(char.upper(), self.letters.get(' ', [' ']))

    def render(self, text):
        """
        Render text as ASCII art
        
        :param text: Text to convert
        :return: Rendered ASCII art as a string
        """
        # Ensure text is uppercase
        text = text.upper()
        
        # Initialize lines for rendering
        art_lines = [''] * 5  # Assuming 5-line height
        
        for char in text:
            # Get character's art or use space if not found
            char_art = self.get_letter(char)
            
            # Combine lines
            for i in range(len(char_art)):
                art_lines[i] += char_art[i] + " "
        
        # Join lines and remove trailing space
        return "\n".join(art_lines)
