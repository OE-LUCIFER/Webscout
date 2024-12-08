"""
Text classification module using rule-based and statistical approaches.
"""

from typing import Dict, List, Set, Tuple
from collections import Counter
import math
import re

from .normalizer import TextNormalizer
from .tokenizer import WordTokenizer


class TextClassifier:
    """Simple text classifier using TF-IDF and cosine similarity."""
    
    def __init__(self):
        self.word_tokenizer = WordTokenizer()
        self.normalizer = TextNormalizer()
        self.documents: Dict[str, List[str]] = {}  # category -> list of documents
        self.vocabulary: Set[str] = set()
        self.idf_scores: Dict[str, float] = {}
        self.category_vectors: Dict[str, Dict[str, float]] = {}
    
    def train(self, documents: Dict[str, List[str]]) -> None:
        """
        Train the classifier on labeled documents.
        
        Args:
            documents: Dict mapping categories to lists of documents
        """
        self.documents = documents
        
        # Build vocabulary and document frequencies
        doc_frequencies: Dict[str, int] = Counter()
        total_docs = sum(len(docs) for docs in documents.values())
        
        for category, docs in documents.items():
            for doc in docs:
                # Normalize and tokenize
                doc = self.normalizer.normalize(doc)
                tokens = self.word_tokenizer.tokenize(doc)
                
                # Update vocabulary and document frequencies
                unique_tokens = set(tokens)
                self.vocabulary.update(unique_tokens)
                doc_frequencies.update(unique_tokens)
        
        # Calculate IDF scores
        self.idf_scores = {
            word: math.log(total_docs / (freq + 1))
            for word, freq in doc_frequencies.items()
        }
        
        # Calculate TF-IDF vectors for each category
        for category, docs in documents.items():
            category_vector: Dict[str, float] = {word: 0.0 for word in self.vocabulary}
            
            for doc in docs:
                # Get term frequencies
                doc = self.normalizer.normalize(doc)
                tokens = self.word_tokenizer.tokenize(doc)
                term_freqs = Counter(tokens)
                
                # Update category vector with TF-IDF scores
                for word, tf in term_freqs.items():
                    if word in self.idf_scores:
                        category_vector[word] += tf * self.idf_scores[word]
            
            # Average the scores
            for word in category_vector:
                category_vector[word] /= len(docs)
            
            self.category_vectors[category] = category_vector
    
    def _calculate_vector(self, text: str) -> Dict[str, float]:
        """Calculate TF-IDF vector for input text."""
        # Normalize and tokenize
        text = self.normalizer.normalize(text)
        tokens = self.word_tokenizer.tokenize(text)
        term_freqs = Counter(tokens)
        
        # Calculate TF-IDF scores
        vector = {word: 0.0 for word in self.vocabulary}
        for word, tf in term_freqs.items():
            if word in self.idf_scores:
                vector[word] = tf * self.idf_scores[word]
        
        return vector
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(vec1[word] * vec2[word] for word in vec1)
        norm1 = math.sqrt(sum(score * score for score in vec1.values()))
        norm2 = math.sqrt(sum(score * score for score in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def classify(self, text: str) -> List[Tuple[str, float]]:
        """
        Classify text into categories with confidence scores.
        
        Returns:
            List of (category, confidence) tuples, sorted by confidence
        """
        if not self.category_vectors:
            raise ValueError("Classifier must be trained before classification")
        
        # Calculate vector for input text
        text_vector = self._calculate_vector(text)
        
        # Calculate similarity with each category
        similarities = [
            (category, self._cosine_similarity(text_vector, category_vec))
            for category, category_vec in self.category_vectors.items()
        ]
        
        # Sort by similarity score
        return sorted(similarities, key=lambda x: x[1], reverse=True)


class TopicClassifier:
    """Rule-based topic classifier using keyword matching."""
    
    def __init__(self):
        # Define topic keywords
        self.topic_keywords = {
            'TECHNOLOGY': {
                'computer', 'software', 'hardware', 'internet', 'programming',
                'digital', 'data', 'algorithm', 'code', 'web', 'app', 'mobile',
                'cyber', 'robot', 'ai', 'artificial intelligence', 'machine learning'
            },
            'SCIENCE': {
                'research', 'experiment', 'laboratory', 'scientific', 'physics',
                'chemistry', 'biology', 'mathematics', 'theory', 'hypothesis',
                'study', 'discovery', 'innovation', 'analysis', 'observation'
            },
            'BUSINESS': {
                'company', 'market', 'finance', 'investment', 'stock', 'trade',
                'economy', 'business', 'corporate', 'startup', 'entrepreneur',
                'profit', 'revenue', 'management', 'strategy', 'commercial'
            },
            'POLITICS': {
                'government', 'policy', 'election', 'political', 'democracy',
                'parliament', 'congress', 'law', 'legislation', 'party',
                'vote', 'campaign', 'president', 'minister', 'diplomatic'
            },
            'SPORTS': {
                'game', 'team', 'player', 'competition', 'tournament',
                'championship', 'score', 'match', 'athlete', 'sport',
                'win', 'lose', 'victory', 'defeat', 'coach', 'training'
            },
            'ENTERTAINMENT': {
                'movie', 'film', 'music', 'song', 'concert', 'actor',
                'actress', 'celebrity', 'show', 'performance', 'art',
                'entertainment', 'theater', 'dance', 'festival', 'media'
            }
        }
        
        # Compile regex patterns for each topic
        self.topic_patterns = {
            topic: re.compile(r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b', re.IGNORECASE)
            for topic, keywords in self.topic_keywords.items()
        }
    
    def classify(self, text: str) -> List[Tuple[str, float]]:
        """
        Classify text into topics with confidence scores.
        
        Returns:
            List of (topic, confidence) tuples, sorted by confidence
        """
        # Count keyword matches for each topic
        topic_matches = {
            topic: len(pattern.findall(text))
            for topic, pattern in self.topic_patterns.items()
        }
        
        # Calculate confidence scores
        total_matches = sum(topic_matches.values()) or 1  # Avoid division by zero
        topic_scores = [
            (topic, count / total_matches)
            for topic, count in topic_matches.items()
        ]
        
        # Sort by score
        return sorted(topic_scores, key=lambda x: x[1], reverse=True)
