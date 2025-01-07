# Webstoken

A pure Python Natural Language Processing (NLP) toolkit that implements common text processing features from scratch, without any external dependencies.

## Features

- **Sentence Tokenization**: Advanced sentence boundary detection with support for:
  - Abbreviations
  - URLs and emails
  - Quoted text
  - Multiple languages
  - Special characters

- **Word Tokenization**: Sophisticated word tokenizer that handles:
  - Contractions (e.g., "don't" → ["do", "not"])
  - Numbers with commas and decimals
  - Hashtags and mentions
  - Punctuation preservation

- **Part-of-Speech Tagging**: Rule-based POS tagger supporting:
  - Common word categories (NOUN, VERB, ADJ, etc.)
  - Suffix analysis
  - Context-aware tagging
  - Special cases (proper nouns, numbers)

- **Stemming**: Porter-like stemming algorithm with:
  - Plural forms handling
  - Past participle processing
  - Common suffix removal
  - Syllable-aware rules

- **Text Normalization**: Utilities for:
  - Stop word removal
  - Case normalization
  - Special character handling
  - Whitespace normalization

## Usage

```python
from webstoken import process_text

# Example text
text = "The quick brown fox's jumping over lazy dogs! Will they catch it?"

# Process text with all features
result = process_text(text)

# Access processed data
for sentence_data in result['sentences']:
    print("Original:", sentence_data['original'])
    print("Tokens:", sentence_data['tokens'])
    print("POS Tags:", sentence_data['pos_tags'])
    print("Stems:", sentence_data['stems'])
    print()

# Get statistics
print(f"Number of sentences: {result['num_sentences']}")
print(f"Total tokens: {result['num_tokens']}")
```

## Individual Components

You can also use individual components:

```python
from webstoken import (
    SentenceTokenizer,
    WordTokenizer,
    POSTagger,
    Stemmer,
    TextNormalizer
)

# Initialize components
sentence_tokenizer = SentenceTokenizer()
word_tokenizer = WordTokenizer()
pos_tagger = POSTagger()
stemmer = Stemmer()
normalizer = TextNormalizer()

# Use them separately
text = "The quick brown fox jumps over the lazy dog."
sentences = sentence_tokenizer.tokenize(text)
for sentence in sentences:
    # Tokenize words
    tokens = word_tokenizer.tokenize(sentence)
    
    # Get POS tags
    pos_tags = pos_tagger.tag(tokens)
    
    # Get word stems
    stems = [stemmer.stem(token) for token in tokens]
    
    # Remove stop words
    clean_tokens = normalizer.remove_stop_words(tokens)
```

## No External Dependencies

All features are implemented from scratch in pure Python, making this package completely self-contained and easy to install.


