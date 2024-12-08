"""
Sentiment analysis module for determining text sentiment and emotion.
"""

from typing import Dict, List, Set, Tuple
import re

from .tokenizer import WordTokenizer
from .normalizer import TextNormalizer


class SentimentAnalyzer:
    """Rule-based sentiment analysis using lexicon approach."""
    
    def __init__(self):
        self.word_tokenizer = WordTokenizer()
        self.normalizer = TextNormalizer()
        
        # Sentiment lexicons
        self.positive_words: Set[str] = {
            'good', 'great', 'awesome', 'excellent', 'happy', 'wonderful',
            'fantastic', 'amazing', 'love', 'beautiful', 'best', 'perfect',
            'brilliant', 'outstanding', 'superb', 'nice', 'pleasant', 'delightful',
            'positive', 'remarkable', 'terrific', 'incredible', 'enjoyable',
            'favorable', 'marvelous', 'splendid', 'superior', 'worthy', 'right'
        }
        
        self.negative_words: Set[str] = {
            'bad', 'terrible', 'awful', 'horrible', 'sad', 'poor', 'wrong',
            'worse', 'worst', 'hate', 'dislike', 'disappointing', 'negative',
            'inferior', 'useless', 'worthless', 'mediocre', 'inadequate',
            'unpleasant', 'unfavorable', 'disagreeable', 'offensive', 'annoying',
            'frustrating', 'irritating', 'disgusting', 'dreadful', 'pathetic'
        }
        
        # Emotion lexicons
        self.emotion_words = {
            'JOY': {
                'happy', 'joyful', 'delighted', 'excited', 'pleased', 'glad',
                'cheerful', 'content', 'satisfied', 'elated', 'jubilant',
                'thrilled', 'ecstatic', 'merry', 'peaceful', 'upbeat'
            },
            'SADNESS': {
                'sad', 'unhappy', 'depressed', 'gloomy', 'miserable', 'down',
                'heartbroken', 'disappointed', 'upset', 'distressed', 'grief',
                'sorrow', 'melancholy', 'despair', 'hopeless', 'blue'
            },
            'ANGER': {
                'angry', 'mad', 'furious', 'outraged', 'irritated', 'annoyed',
                'frustrated', 'enraged', 'hostile', 'bitter', 'hateful', 'rage',
                'resentful', 'violent', 'aggressive', 'irate'
            },
            'FEAR': {
                'afraid', 'scared', 'frightened', 'terrified', 'anxious', 'worried',
                'nervous', 'fearful', 'panicked', 'alarmed', 'horrified', 'dread',
                'uneasy', 'stressed', 'concerned', 'apprehensive'
            },
            'SURPRISE': {
                'surprised', 'amazed', 'astonished', 'shocked', 'stunned',
                'startled', 'unexpected', 'incredible', 'unbelievable', 'wonder',
                'awe', 'remarkable', 'mysterious', 'sudden', 'strange'
            }
        }
        
        # Intensity modifiers
        self.intensifiers = {
            'very': 1.5,
            'really': 1.5,
            'extremely': 2.0,
            'incredibly': 2.0,
            'absolutely': 2.0,
            'totally': 1.5,
            'completely': 1.5,
            'utterly': 2.0,
            'highly': 1.5,
            'especially': 1.5
        }
        
        self.diminishers = {
            'somewhat': 0.5,
            'slightly': 0.5,
            'barely': 0.3,
            'hardly': 0.3,
            'sort of': 0.5,
            'kind of': 0.5,
            'a bit': 0.5,
            'a little': 0.5,
            'not very': 0.3,
            'less': 0.5
        }
        
        # Negation words
        self.negation_words = {
            'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither',
            'nowhere', 'hardly', 'scarcely', 'barely', "don't", "doesn't",
            "didn't", "won't", "wouldn't", "shouldn't", "couldn't", "can't"
        }
        
        # Compile patterns
        self.word_pattern = re.compile(r'\b\w+\b')
    
    def _get_window_around_word(self, words: List[str], index: int, window_size: int = 3) -> List[str]:
        """Get a window of words around a given index."""
        start = max(0, index - window_size)
        end = min(len(words), index + window_size + 1)
        return words[start:end]
    
    def _is_negated(self, words: List[str], index: int) -> bool:
        """Check if a word is negated by looking at surrounding context."""
        window = self._get_window_around_word(words, index)
        return any(word in self.negation_words for word in window[:index-window[0]])
    
    def _get_intensity_multiplier(self, words: List[str], index: int) -> float:
        """Get intensity multiplier based on modifiers."""
        window = self._get_window_around_word(words, index)
        multiplier = 1.0
        
        for word in window[:index-window[0]]:
            if word in self.intensifiers:
                multiplier *= self.intensifiers[word]
            elif word in self.diminishers:
                multiplier *= self.diminishers[word]
        
        return multiplier
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.
        
        Returns:
            Dict with sentiment scores:
            {
                'polarity': float (-1 to 1),
                'subjectivity': float (0 to 1),
                'confidence': float (0 to 1)
            }
        """
        # Normalize and tokenize text
        text = self.normalizer.normalize(text)
        words = self.word_tokenizer.tokenize(text)
        
        positive_score = 0
        negative_score = 0
        word_count = len(words)
        
        for i, word in enumerate(words):
            word = word.lower()
            multiplier = self._get_intensity_multiplier(words, i)
            is_negated = self._is_negated(words, i)
            
            if word in self.positive_words:
                score = 1.0 * multiplier
                positive_score += -score if is_negated else score
            elif word in self.negative_words:
                score = 1.0 * multiplier
                negative_score += -score if is_negated else score
        
        # Calculate metrics
        total_score = positive_score + negative_score
        total_magnitude = abs(positive_score) + abs(negative_score)
        
        if word_count == 0:
            return {'polarity': 0.0, 'subjectivity': 0.0, 'confidence': 0.0}
        
        polarity = total_score / (word_count or 1)  # Normalize to [-1, 1]
        subjectivity = total_magnitude / (word_count or 1)  # Normalize to [0, 1]
        confidence = min(1.0, total_magnitude / (word_count / 2))  # Confidence based on magnitude
        
        return {
            'polarity': max(-1.0, min(1.0, polarity)),
            'subjectivity': min(1.0, subjectivity),
            'confidence': confidence
        }
    
    def analyze_emotions(self, text: str) -> List[Tuple[str, float]]:
        """
        Analyze emotions in text.
        
        Returns:
            List of (emotion, score) tuples, sorted by score
        """
        # Normalize and tokenize text
        text = self.normalizer.normalize(text)
        words = self.word_tokenizer.tokenize(text)
        
        emotion_scores = {emotion: 0.0 for emotion in self.emotion_words}
        
        for i, word in enumerate(words):
            word = word.lower()
            multiplier = self._get_intensity_multiplier(words, i)
            is_negated = self._is_negated(words, i)
            
            for emotion, emotion_set in self.emotion_words.items():
                if word in emotion_set:
                    score = 1.0 * multiplier
                    emotion_scores[emotion] += -score if is_negated else score
        
        # Normalize scores
        max_score = max(abs(score) for score in emotion_scores.values()) or 1
        normalized_scores = [
            (emotion, score/max_score)
            for emotion, score in emotion_scores.items()
        ]
        
        # Sort by score
        return sorted(normalized_scores, key=lambda x: x[1], reverse=True)
