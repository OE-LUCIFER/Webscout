"""
Text normalization utilities.
"""

import re
from typing import List, Set


class TextNormalizer:
    """Text normalization utilities."""
    
    def __init__(self):
        self.stop_words: Set[str] = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with'
        }
        
    def remove_stop_words(self, tokens: List[str]) -> List[str]:
        """Remove common stop words from token list."""
        return [token for token in tokens if token.lower() not in self.stop_words]
    
    def normalize(self, text: str) -> str:
        """Apply various normalization steps to text."""
        # Convert to lowercase
        text = text.lower()
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters except apostrophes within words
        text = re.sub(r'[^a-z0-9\s\']', '', text)
        text = re.sub(r'\s\'|\'\s', ' ', text)
        
        return text.strip()
