"""
Named Entity Recognition (NER) module for identifying and classifying named entities.
"""

from typing import List, Tuple, Dict, Set
import re


class NamedEntityRecognizer:
    """Rule-based Named Entity Recognition."""
    
    def __init__(self):
        # Common entity patterns
        self.PERSON_TITLES = {
            'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'sir', 'madam',
            'lord', 'lady', 'president', 'ceo', 'director'
        }
        
        self.ORGANIZATION_SUFFIXES = {
            'inc', 'corp', 'ltd', 'llc', 'company', 'corporation',
            'associates', 'partners', 'foundation', 'institute'
        }
        
        self.LOCATION_INDICATORS = {
            'street', 'road', 'avenue', 'boulevard', 'lane', 'drive',
            'circle', 'square', 'park', 'bridge', 'river', 'lake',
            'mountain', 'forest', 'city', 'town', 'village', 'country'
        }
        
        self.DATE_MONTHS = {
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        }
        
        # Compile regex patterns
        self.patterns = {
            'EMAIL': re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w+\b'),
            'URL': re.compile(r'https?://(?:[\w-]|(?:%[\da-fA-F]{2}))+'),
            'PHONE': re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            'DATE': re.compile(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'),
            'TIME': re.compile(r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?\b'),
            'MONEY': re.compile(r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|USD|EUR|GBP)'),
            'PERCENTAGE': re.compile(r'\b\d+(?:\.\d+)?%\b')
        }
    
    def is_capitalized(self, word: str) -> bool:
        """Check if a word is capitalized."""
        return word and word[0].isupper()
    
    def extract_entities(self, text: str) -> Dict[str, List[Tuple[str, str]]]:
        """
        Extract named entities from text.
        
        Returns:
            Dict mapping entity types to list of (text, label) tuples
        """
        entities = {
            'PERSON': [],
            'ORGANIZATION': [],
            'LOCATION': [],
            'DATE': [],
            'TIME': [],
            'MONEY': [],
            'EMAIL': [],
            'URL': [],
            'PHONE': [],
            'PERCENTAGE': []
        }
        
        # First find regex pattern matches
        for label, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                entities[label].append((match.group(), label))
        
        # Process text word by word for other entities
        words = text.split()
        i = 0
        while i < len(words):
            word = words[i]
            next_word = words[i + 1] if i + 1 < len(words) else None
            
            # Check for person names
            if word.lower() in self.PERSON_TITLES and next_word and self.is_capitalized(next_word):
                name_parts = []
                j = i + 1
                while j < len(words) and self.is_capitalized(words[j]):
                    name_parts.append(words[j])
                    j += 1
                if name_parts:
                    entities['PERSON'].append((' '.join(name_parts), 'PERSON'))
                i = j
                continue
            
            # Check for organizations
            if self.is_capitalized(word):
                org_parts = [word]
                j = i + 1
                while j < len(words) and (
                    self.is_capitalized(words[j]) or 
                    words[j].lower() in self.ORGANIZATION_SUFFIXES
                ):
                    org_parts.append(words[j])
                    j += 1
                if len(org_parts) > 1 or (
                    len(org_parts) == 1 and 
                    any(suff in word.lower() for suff in self.ORGANIZATION_SUFFIXES)
                ):
                    entities['ORGANIZATION'].append((' '.join(org_parts), 'ORGANIZATION'))
                i = j
                continue
            
            # Check for locations
            if word.lower() in self.LOCATION_INDICATORS and i > 0:
                if self.is_capitalized(words[i - 1]):
                    entities['LOCATION'].append((words[i - 1] + ' ' + word, 'LOCATION'))
            
            i += 1
        
        return entities
        
    def tag_text(self, text: str) -> List[Tuple[str, str]]:
        """
        Tag each word in text with its entity type.
        
        Returns:
            List of (word, entity_type) tuples
        """
        entities = self.extract_entities(text)
        tagged = []
        
        # Create a map of word positions to entity labels
        position_labels = {}
        text_lower = text.lower()
        
        for entity_type, entity_list in entities.items():
            for entity_text, _ in entity_list:
                start = text_lower.find(entity_text.lower())
                if start != -1:
                    end = start + len(entity_text)
                    for pos in range(start, end):
                        position_labels[pos] = entity_type
        
        # Tag each character position
        current_pos = 0
        current_word = []
        current_label = 'O'  # Outside any entity
        
        for char in text:
            if char.isspace():
                if current_word:
                    tagged.append((''.join(current_word), current_label))
                    current_word = []
                    current_label = 'O'
            else:
                current_word.append(char)
                if current_pos in position_labels:
                    current_label = position_labels[current_pos]
            current_pos += 1
        
        # Add last word if exists
        if current_word:
            tagged.append((''.join(current_word), current_label))
        
        return tagged
