"""
Main text processing utilities combining all NLP components.
"""

from typing import Dict, Any, List, Tuple

from .tokenizer import SentenceTokenizer, WordTokenizer
from .tagger import POSTagger
from .stemmer import Stemmer
from .normalizer import TextNormalizer


def process_text(text: str, normalize: bool = True, remove_stops: bool = True) -> Dict[str, Any]:
    """
    Process text using all available NLP tools.
    
    Args:
        text (str): Input text to process
        normalize (bool): Whether to normalize text
        remove_stops (bool): Whether to remove stop words
        
    Returns:
        Dict containing processed results with the following structure:
        {
            'sentences': [
                {
                    'original': str,     # Original sentence
                    'tokens': List[str],  # Word tokens
                    'pos_tags': List[Tuple[str, str]],  # (word, tag) pairs
                    'stems': List[Tuple[str, str]]      # (word, stem) pairs
                },
                ...
            ],
            'num_sentences': int,  # Total number of sentences
            'num_tokens': int      # Total number of tokens
        }
    """
    # Initialize tools
    sentence_tokenizer = SentenceTokenizer()
    word_tokenizer = WordTokenizer()
    pos_tagger = POSTagger()
    stemmer = Stemmer()
    normalizer = TextNormalizer()
    
    # Process text
    if normalize:
        text = normalizer.normalize(text)
    
    # Get sentences
    sentences = sentence_tokenizer.tokenize(text)
    
    # Process each sentence
    processed_sentences = []
    for sentence in sentences:
        # Tokenize words
        tokens = word_tokenizer.tokenize(sentence)
        
        # Remove stop words if requested
        if remove_stops:
            tokens = normalizer.remove_stop_words(tokens)
        
        # Get POS tags and stems
        tagged = pos_tagger.tag(tokens)
        stems = [(token, stemmer.stem(token)) for token, _ in tagged]
        
        processed_sentences.append({
            'original': sentence,
            'tokens': tokens,
            'pos_tags': tagged,
            'stems': stems
        })
    
    return {
        'sentences': processed_sentences,
        'num_sentences': len(sentences),
        'num_tokens': sum(len(s['tokens']) for s in processed_sentences)
    }
