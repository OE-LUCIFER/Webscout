"""
Language detection module using character and word frequency analysis.
"""

from typing import Dict, List, Set, Tuple
from collections import Counter
import re


class LanguageDetector:
    """Language detection using character n-gram frequencies."""
    
    def __init__(self):
        # Language profiles based on common character sequences
        self.language_profiles = {
            'ENGLISH': {
                'chars': 'etaoinshrdlcumwfgypbvkjxqz',
                'ngrams': {'th', 'he', 'in', 'er', 'an', 're', 'on', 'at', 'en', 'nd',
                          'ti', 'es', 'or', 'te', 'of', 'ed', 'is', 'it', 'al', 'ar',
                          'st', 'to', 'nt', 'ng', 'se', 'ha', 'as', 'ou', 'io', 'le'},
                'words': {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
                         'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
                         'do', 'at'}
            },
            'SPANISH': {
                'chars': 'eaosrnidlctumpbgvyqhfzjñxwk',
                'ngrams': {'de', 'en', 'el', 'la', 'os', 'es', 'as', 'ar', 'er', 'ra',
                          'al', 'an', 'do', 'or', 'ta', 'ue', 'io', 'on', 'ro', 'ad',
                          'te', 'co', 'st', 'ci', 'nt', 'to', 'lo', 'no', 'po', 'ac'},
                'words': {'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'se', 'del',
                         'las', 'un', 'por', 'con', 'no', 'una', 'su', 'para', 'es',
                         'al'}
            },
            'FRENCH': {
                'chars': 'esaitnrulodcpmévqfbghàjxèêyçwzùâîôûëïüœ',
                'ngrams': {'es', 'le', 'en', 'de', 'nt', 'on', 're', 'er', 'ai', 'te',
                          'la', 'an', 'ou', 'it', 'ur', 'et', 'el', 'se', 'qu', 'me',
                          'is', 'ar', 'ce', 'ns', 'us', 'ue', 'ss', 'ie', 'em', 'tr'},
                'words': {'le', 'de', 'un', 'être', 'et', 'à', 'il', 'avoir', 'ne',
                         'je', 'son', 'que', 'se', 'qui', 'ce', 'dans', 'en', 'du',
                         'elle', 'au'}
            },
            'GERMAN': {
                'chars': 'enisratdhulcgmobwfkzvüpäößjyqxéèêëàáâãåāăąćčĉċďđ',
                'ngrams': {'en', 'er', 'ch', 'de', 'ei', 'in', 'te', 'nd', 'ie', 'ge',
                          'st', 'ne', 'be', 'es', 'un', 'zu', 'an', 'ng', 'au', 'it',
                          'is', 'he', 'ht', 'se', 'ck', 'ic', 're', 'ns', 'sc', 'tz'},
                'words': {'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit',
                         'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht',
                         'ein', 'eine', 'als'}
            }
        }
        
        # Compile word patterns
        self.word_pattern = re.compile(r'\b\w+\b')
    
    def _extract_ngrams(self, text: str, n: int = 2) -> List[str]:
        """Extract character n-grams from text."""
        text = text.lower()
        return [text[i:i+n] for i in range(len(text)-n+1)]
    
    def _calculate_char_frequencies(self, text: str) -> Dict[str, float]:
        """Calculate character frequencies in text."""
        text = text.lower()
        char_count = Counter(c for c in text if c.isalpha())
        total = sum(char_count.values()) or 1
        return {char: count/total for char, count in char_count.items()}
    
    def _calculate_ngram_frequencies(self, text: str) -> Dict[str, float]:
        """Calculate n-gram frequencies in text."""
        ngrams = self._extract_ngrams(text)
        ngram_count = Counter(ngrams)
        total = sum(ngram_count.values()) or 1
        return {ngram: count/total for ngram, count in ngram_count.items()}
    
    def _calculate_word_frequencies(self, text: str) -> Dict[str, float]:
        """Calculate word frequencies in text."""
        words = self.word_pattern.findall(text.lower())
        word_count = Counter(words)
        total = sum(word_count.values()) or 1
        return {word: count/total for word, count in word_count.items()}
    
    def _calculate_similarity(self, freq1: Dict[str, float], freq2: Dict[str, float]) -> float:
        """Calculate similarity between two frequency distributions."""
        common_keys = set(freq1.keys()) & set(freq2.keys())
        if not common_keys:
            return 0.0
        
        similarity = sum(min(freq1.get(k, 0), freq2.get(k, 0)) for k in common_keys)
        return similarity
    
    def detect(self, text: str) -> List[Tuple[str, float]]:
        """
        Detect the language of text with confidence scores.
        
        Returns:
            List of (language, confidence) tuples, sorted by confidence
        """
        if not text:
            return []
        
        # Calculate frequencies for input text
        char_freqs = self._calculate_char_frequencies(text)
        ngram_freqs = self._calculate_ngram_frequencies(text)
        word_freqs = self._calculate_word_frequencies(text)
        
        # Calculate similarity scores for each language
        scores = []
        for lang, profile in self.language_profiles.items():
            # Character similarity
            char_sim = sum(char_freqs.get(c, 0) for c in profile['chars'])
            
            # N-gram similarity
            ngram_sim = sum(ngram_freqs.get(ng, 0) for ng in profile['ngrams'])
            
            # Word similarity
            word_sim = sum(word_freqs.get(w, 0) for w in profile['words'])
            
            # Combined score (weighted average)
            total_score = (0.3 * char_sim + 0.4 * ngram_sim + 0.3 * word_sim)
            scores.append((lang, total_score))
        
        # Normalize scores
        total = sum(score for _, score in scores) or 1
        normalized_scores = [(lang, score/total) for lang, score in scores]
        
        # Sort by confidence
        return sorted(normalized_scores, key=lambda x: x[1], reverse=True)
