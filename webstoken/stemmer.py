"""
Word stemming utilities.
"""

from typing import Set


class Stemmer:
    """Simple rule-based stemmer implementing Porter-like rules."""
    
    def __init__(self):
        self.vowels: Set[str] = {'a', 'e', 'i', 'o', 'u', 'y'}
        self.doubles: Set[str] = {'bb', 'dd', 'ff', 'gg', 'mm', 'nn', 'pp', 'rr', 'tt'}
        
    def is_vowel(self, char: str, prev_char: str = None) -> bool:
        """Check if a character is a vowel, considering 'y' special cases."""
        return char in self.vowels or (char == 'y' and prev_char and prev_char not in self.vowels)
    
    def count_syllables(self, word: str) -> int:
        """Count syllables in a word based on vowel sequences."""
        count = 0
        prev_char = None
        for i, char in enumerate(word.lower()):
            if self.is_vowel(char, prev_char) and (i == 0 or not self.is_vowel(prev_char, word[i-2] if i > 1 else None)):
                count += 1
            prev_char = char
        return count or 1
    
    def stem(self, word: str) -> str:
        """Apply stemming rules to reduce word to its root form."""
        if len(word) <= 3:
            return word
            
        word = word.lower()
        
        # Step 1: Handle plurals and past participles
        if word.endswith('sses'):
            word = word[:-2]
        elif word.endswith('ies'):
            word = word[:-2]
        elif word.endswith('ss'):
            pass
        elif word.endswith('s') and len(word) > 4:
            word = word[:-1]
            
        # Step 2: Handle -ed and -ing
        if word.endswith('ed') and self.count_syllables(word[:-2]) > 1:
            word = word[:-2]
        elif word.endswith('ing') and self.count_syllables(word[:-3]) > 1:
            word = word[:-3]
            
        # Step 3: Handle miscellaneous endings
        if len(word) > 5:
            if word.endswith('ement'):
                word = word[:-5]
            elif word.endswith('ment'):
                word = word[:-4]
            elif word.endswith('ent'):
                word = word[:-3]
                
        # Step 4: Handle -ity endings
        if word.endswith('ity') and len(word) > 6:
            word = word[:-3]
            if word.endswith('abil'):
                word = word[:-4] + 'able'
            elif word.endswith('ic'):
                word = word[:-2]
                
        # Final step: Remove double consonants at the end
        if len(word) > 2 and word[-2:] in self.doubles:
            word = word[:-1]
            
        return word
