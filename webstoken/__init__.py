"""
Webstoken - A pure Python NLP toolkit for text processing
"""

from .tokenizer import SentenceTokenizer, WordTokenizer
from .tagger import POSTagger
from .stemmer import Stemmer
from .normalizer import TextNormalizer
from .processor import process_text
from .ner import NamedEntityRecognizer
from .classifier import TextClassifier, TopicClassifier
from .language import LanguageDetector
from .sentiment import SentimentAnalyzer
from .keywords import KeywordExtractor

__version__ = '0.1.0'
__all__ = [
    'SentenceTokenizer',
    'WordTokenizer',
    'POSTagger',
    'Stemmer',
    'TextNormalizer',
    'process_text',
    'NamedEntityRecognizer',
    'TextClassifier',
    'TopicClassifier',
    'LanguageDetector',
    'SentimentAnalyzer',
    'KeywordExtractor'
]
