"""
Part-of-Speech tagging utilities.
"""

from typing import List, Set, Tuple


class POSTagger:
    """Simple rule-based Part-of-Speech tagger."""
    
    def __init__(self):
        # Basic rules for POS tagging
        self.noun_suffixes: Set[str] = {'ness', 'ment', 'ship', 'dom', 'hood', 'er', 'or', 'ist'}
        self.verb_suffixes: Set[str] = {'ize', 'ate', 'ify', 'ing', 'ed'}
        self.adj_suffixes: Set[str] = {'able', 'ible', 'al', 'ful', 'ous', 'ive', 'less'}
        self.adv_suffixes: Set[str] = {'ly'}
        
        # Common words by POS
        self.determiners: Set[str] = {'the', 'a', 'an', 'this', 'that', 'these', 'those'}
        self.prepositions: Set[str] = {'in', 'on', 'at', 'by', 'with', 'from', 'to', 'for'}
        self.pronouns: Set[str] = {'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her'}
        
    def tag(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """Assign POS tags to tokens based on rules."""
        tagged = []
        prev_tag = None
        
        for i, token in enumerate(tokens):
            word = token.lower()
            
            # Check special cases first
            if word in self.determiners:
                tag = 'DET'
            elif word in self.prepositions:
                tag = 'PREP'
            elif word in self.pronouns:
                tag = 'PRON'
            # Check suffixes
            elif any(word.endswith(suffix) for suffix in self.noun_suffixes):
                tag = 'NOUN'
            elif any(word.endswith(suffix) for suffix in self.verb_suffixes):
                tag = 'VERB'
            elif any(word.endswith(suffix) for suffix in self.adj_suffixes):
                tag = 'ADJ'
            elif any(word.endswith(suffix) for suffix in self.adv_suffixes):
                tag = 'ADV'
            # Default cases
            elif word[0].isupper() and i > 0:
                tag = 'PROPN'  # Proper noun
            elif word.isdigit():
                tag = 'NUM'
            elif not word.isalnum():
                tag = 'PUNCT'
            else:
                tag = 'NOUN'  # Default to noun
            
            tagged.append((token, tag))
            prev_tag = tag
            
        return tagged
