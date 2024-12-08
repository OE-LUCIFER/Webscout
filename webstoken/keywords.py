"""
Keyword extraction module using statistical and graph-based approaches.
"""

from typing import Dict, List, Set, Tuple
from collections import Counter, defaultdict
import math
import re

from .tokenizer import WordTokenizer
from .normalizer import TextNormalizer


class KeywordExtractor:
    """Keyword extraction using TF-IDF and TextRank-inspired algorithms."""
    
    def __init__(self):
        self.word_tokenizer = WordTokenizer()
        self.normalizer = TextNormalizer()
        
        # Common words to filter out beyond basic stop words
        self.filter_words: Set[str] = {
            'would', 'could', 'should', 'said', 'also', 'may', 'might',
            'must', 'need', 'shall', 'want', 'way', 'time', 'just',
            'now', 'like', 'make', 'made', 'well', 'back', 'even',
            'still', 'way', 'take', 'took', 'get', 'got', 'go', 'went'
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple rules."""
        text = re.sub(r'\s+', ' ', text)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_word_scores(self, text: str) -> Dict[str, float]:
        """Calculate word importance scores using frequency and position."""
        # Normalize and tokenize text
        text = self.normalizer.normalize(text)
        sentences = self._split_into_sentences(text)
        
        word_scores: Dict[str, float] = defaultdict(float)
        word_positions: Dict[str, List[int]] = defaultdict(list)
        
        # Calculate word frequencies and positions
        for i, sentence in enumerate(sentences):
            words = self.word_tokenizer.tokenize(sentence)
            for j, word in enumerate(words):
                word = word.lower()
                if (word.isalnum() and 
                    len(word) > 2 and
                    word not in self.filter_words and
                    word not in self.normalizer.stop_words):
                    word_scores[word] += 1
                    word_positions[word].append(i)
        
        # Adjust scores based on position
        num_sentences = len(sentences)
        for word, positions in word_positions.items():
            # Words appearing in first or last sentences get bonus
            if 0 in positions:
                word_scores[word] *= 1.2
            if num_sentences - 1 in positions:
                word_scores[word] *= 1.1
            
            # Words appearing throughout text get bonus
            coverage = len(set(positions)) / num_sentences
            word_scores[word] *= (1 + coverage)
        
        return word_scores
    
    def _calculate_word_cooccurrence(self, text: str, window_size: int = 3) -> Dict[str, Dict[str, int]]:
        """Calculate word co-occurrence matrix."""
        # Normalize and tokenize text
        text = self.normalizer.normalize(text)
        words = self.word_tokenizer.tokenize(text)
        
        # Filter words
        filtered_words = [
            word.lower() for word in words
            if (word.isalnum() and
                len(word) > 2 and
                word.lower() not in self.filter_words and
                word.lower() not in self.normalizer.stop_words)
        ]
        
        # Build co-occurrence matrix
        cooccurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for i, word in enumerate(filtered_words):
            for j in range(max(0, i - window_size), min(len(filtered_words), i + window_size + 1)):
                if i != j:
                    cooccurrence[word][filtered_words[j]] += 1
                    cooccurrence[filtered_words[j]][word] += 1
        
        return cooccurrence
    
    def _textrank_scores(self, cooccurrence: Dict[str, Dict[str, int]], damping: float = 0.85,
                        iterations: int = 30) -> Dict[str, float]:
        """Calculate TextRank scores from co-occurrence matrix."""
        scores = {word: 1.0 for word in cooccurrence}
        
        for _ in range(iterations):
            new_scores = {}
            for word in scores:
                if not cooccurrence[word]:
                    continue
                    
                incoming_score = sum(
                    scores[other] * cooccurrence[word][other] / sum(cooccurrence[other].values())
                    for other in cooccurrence[word]
                )
                new_scores[word] = (1 - damping) + damping * incoming_score
            
            # Check convergence
            score_diff = sum(abs(new_scores[w] - scores[w]) for w in scores)
            scores = new_scores
            if score_diff < 0.0001:
                break
        
        return scores
    
    def extract_keywords(self, text: str, num_keywords: int = 10,
                        use_textrank: bool = True) -> List[Tuple[str, float]]:
        """
        Extract keywords from text using combined frequency and graph-based approach.
        
        Args:
            text: Input text
            num_keywords: Number of keywords to return
            use_textrank: Whether to use TextRank algorithm
            
        Returns:
            List of (keyword, score) tuples, sorted by score
        """
        if not text:
            return []
        
        # Get frequency-based scores
        freq_scores = self._calculate_word_scores(text)
        
        if use_textrank:
            # Get TextRank scores
            cooccurrence = self._calculate_word_cooccurrence(text)
            textrank_scores = self._textrank_scores(cooccurrence)
            
            # Combine scores
            combined_scores = {
                word: freq_scores[word] * textrank_scores.get(word, 0)
                for word in freq_scores
            }
        else:
            combined_scores = freq_scores
        
        # Sort and return top keywords
        sorted_words = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_words[:num_keywords]
    
    def extract_keyphrases(self, text: str, num_phrases: int = 5,
                          min_words: int = 2, max_words: int = 4) -> List[Tuple[str, float]]:
        """
        Extract key phrases from text.
        
        Args:
            text: Input text
            num_phrases: Number of phrases to return
            min_words: Minimum words in phrase
            max_words: Maximum words in phrase
            
        Returns:
            List of (phrase, score) tuples, sorted by score
        """
        # Normalize and split into sentences
        text = self.normalizer.normalize(text)
        sentences = self._split_into_sentences(text)
        
        # Get word importance scores
        word_scores = self._calculate_word_scores(text)
        
        # Extract candidate phrases
        phrases: Dict[str, float] = {}
        
        for sentence in sentences:
            words = self.word_tokenizer.tokenize(sentence)
            
            # Generate phrases of different lengths
            for i in range(len(words)):
                for length in range(min_words, min(max_words + 1, len(words) - i + 1)):
                    phrase_words = words[i:i+length]
                    
                    # Filter phrases
                    if all(
                        word.isalnum() and
                        len(word) > 2 and
                        word.lower() not in self.filter_words and
                        word.lower() not in self.normalizer.stop_words
                        for word in phrase_words
                    ):
                        phrase = ' '.join(phrase_words)
                        # Score is average of word scores
                        score = sum(word_scores.get(word.lower(), 0) for word in phrase_words)
                        score /= len(phrase_words)
                        phrases[phrase] = score
        
        # Sort and return top phrases
        sorted_phrases = sorted(
            phrases.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_phrases[:num_phrases]
