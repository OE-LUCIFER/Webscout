"""
Tokenization utilities for sentence and word-level tokenization.
"""

from typing import List, Dict, Set, Pattern
import re


class SentenceTokenizer:
    """Advanced sentence tokenizer with support for complex cases and proper formatting."""
    
    def __init__(self) -> None:
        # Common abbreviations by category
        self.TITLES: Set[str] = {
            'mr', 'mrs', 'ms', 'dr', 'prof', 'rev', 'sr', 'jr', 'esq',
            'hon', 'pres', 'gov', 'atty', 'supt', 'det', 'rev', 'col','maj', 'gen', 'capt', 'cmdr',
            'lt', 'sgt', 'cpl', 'pvt'
        }
        
        self.ACADEMIC: Set[str] = {
            'ph.d', 'phd', 'm.d', 'md', 'b.a', 'ba', 'm.a', 'ma', 'd.d.s', 'dds',
            'm.b.a', 'mba', 'b.sc', 'bsc', 'm.sc', 'msc', 'llb', 'll.b', 'bl'
        }
        
        self.ORGANIZATIONS: Set[str] = {
            'inc', 'ltd', 'co', 'corp', 'llc', 'llp', 'assn', 'bros', 'plc', 'cos',
            'intl', 'dept', 'est', 'dist', 'mfg', 'div'
        }
        
        self.MONTHS: Set[str] = {
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        }
        
        self.UNITS: Set[str] = {
            'oz', 'pt', 'qt', 'gal', 'ml', 'cc', 'km', 'cm', 'mm', 'ft', 'in',
            'kg', 'lb', 'lbs', 'hz', 'khz', 'mhz', 'ghz', 'kb', 'mb', 'gb', 'tb'
        }
        
        self.TECHNOLOGY: Set[str] = {
            'v', 'ver', 'app', 'sys', 'dir', 'exe', 'lib', 'api', 'sdk', 'url',
            'cpu', 'gpu', 'ram', 'rom', 'hdd', 'ssd', 'lan', 'wan', 'sql', 'html'
        }
        
        self.MISC: Set[str] = {
            'vs', 'etc', 'ie', 'eg', 'no', 'al', 'ca', 'cf', 'pp', 'est', 'st',
            'approx', 'appt', 'apt', 'dept', 'depts', 'min', 'max', 'avg'
        }

        # Combine all abbreviations
        self.all_abbreviations: Set[str] = (
            self.TITLES | self.ACADEMIC | self.ORGANIZATIONS |
            self.MONTHS | self.UNITS | self.TECHNOLOGY | self.MISC
        )

        # Special patterns
        self.ELLIPSIS: str = r'\.{2,}|…'
        self.URL_PATTERN: str = (
            r'(?:https?:\/\/|www\.)[\w\-\.]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?'
        )
        self.EMAIL_PATTERN: str = r'[\w\.-]+@[\w\.-]+\.\w+'
        self.NUMBER_PATTERN: str = (
            r'\d+(?:\.\d+)?(?:%|°|km|cm|mm|m|kg|g|lb|ft|in|mph|kmh|hz|mhz|ghz)?'
        )
        
        # Quote and bracket pairs
        self.QUOTE_PAIRS: Dict[str, str] = {
            '"': '"', "'": "'", '"': '"', "「": "」", "『": "』",
            "«": "»", "‹": "›", "'": "'", "‚": "'"
        }
        
        self.BRACKETS: Dict[str, str] = {
            '(': ')', '[': ']', '{': '}', '⟨': '⟩', '「': '」',
            '『': '』', '【': '】', '〖': '〗', '｢': '｣'
        }

        # Compile regex patterns
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for better performance."""
        # Pattern for finding potential sentence boundaries
        self.SENTENCE_END: Pattern = re.compile(
            r'''
            # Group for sentence endings
            (?:
                # Standard endings with optional quotes/brackets
                (?<=[.!?])[\"\'\)\]\}»›」』\s]*
                
                # Ellipsis
                |(?:\.{2,}|…)
                
                # Asian-style endings
                |(?<=[。！？」』】\s])
            )
            
            # Must be followed by whitespace and capital letter or number
            (?=\s+(?:[A-Z0-9]|["'({[\[「『《‹〈][A-Z]))
            ''',
            re.VERBOSE
        )

        # Pattern for abbreviations
        abbrev_pattern = '|'.join(re.escape(abbr) for abbr in self.all_abbreviations)
        self.ABBREV_PATTERN: Pattern = re.compile(
            fr'\b(?:{abbrev_pattern})\.?',
            re.IGNORECASE
        )

    def tokenize(self, text: str) -> List[str]:
        """Split text into sentences while handling complex cases."""
        if not text or not text.strip():
            return []
            
        # Initial split on potential sentence boundaries
        sentences = self.SENTENCE_END.split(text)
        
        # Clean and validate sentences
        final_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                final_sentences.append(sentence)
                
        return final_sentences


class WordTokenizer:
    """Simple but effective word tokenizer with support for contractions and special cases."""
    
    def __init__(self):
        self.contractions = {
            "n't": "not", "'ll": "will", "'re": "are", "'s": "is",
            "'m": "am", "'ve": "have", "'d": "would"
        }
        
        self.word_pattern = re.compile(r"""
            (?:[A-Za-z]+(?:[''][A-Za-z]+)*)|    # Words with optional internal apostrophes
            (?:\d+(?:,\d{3})*(?:\.\d+)?)|       # Numbers with commas and decimals
            (?:[@#]?\w+)|                        # Hashtags and mentions
            (?:[^\w\s])                          # Punctuation and symbols
        """, re.VERBOSE)
    
    def tokenize(self, text: str) -> List[str]:
        """Split text into words while handling contractions and special cases."""
        tokens = []
        for match in self.word_pattern.finditer(text):
            word = match.group()
            # Handle contractions
            for contraction, expansion in self.contractions.items():
                if word.endswith(contraction):
                    base = word[:-len(contraction)]
                    if base:
                        tokens.append(base)
                    tokens.append(expansion)
                    break
            else:
                tokens.append(word)
        return tokens
