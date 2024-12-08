from webstoken import (
    process_text, NamedEntityRecognizer, TextClassifier,
    TopicClassifier, LanguageDetector, SentimentAnalyzer,
    KeywordExtractor
)
from rich import print
# Example text
text = """
Dr. John Smith from Microsoft Corporation visited New York City on January 15th, 2024.
He presented an excellent paper about artificial intelligence and machine learning at
the International Technology Conference. The research was incredibly well-received,
and many attendees were excited about its potential applications in healthcare.
"""

print("1. Basic Text Processing")
print("-" * 50)
result = process_text(text)
for sentence_data in result['sentences']:
    print("Original:", sentence_data['original'])
    print("Tokens:", sentence_data['tokens'])
    print("POS Tags:", sentence_data['pos_tags'])
    print("Stems:", sentence_data['stems'])
    print()

print("\n2. Named Entity Recognition")
print("-" * 50)
ner = NamedEntityRecognizer()
entities = ner.extract_entities(text)
for entity_type, entity_list in entities.items():
    if entity_list:
        print(f"{entity_type}:", entity_list)

print("\n3. Topic Classification")
print("-" * 50)
topic_classifier = TopicClassifier()
topics = topic_classifier.classify(text)
print("Topics (with confidence):")
for topic, confidence in topics[:3]:  # Top 3 topics
    print(f"{topic}: {confidence:.2f}")

print("\n4. Language Detection")
print("-" * 50)
lang_detector = LanguageDetector()
languages = lang_detector.detect(text)
print("Detected Languages (with confidence):")
for lang, confidence in languages:
    print(f"{lang}: {confidence:.2f}")

print("\n5. Sentiment Analysis")
print("-" * 50)
sentiment_analyzer = SentimentAnalyzer()
sentiment = sentiment_analyzer.analyze_sentiment(text)
print("Sentiment Scores:")
print(f"Polarity: {sentiment['polarity']:.2f}")
print(f"Subjectivity: {sentiment['subjectivity']:.2f}")
print(f"Confidence: {sentiment['confidence']:.2f}")

print("\nEmotions:")
emotions = sentiment_analyzer.analyze_emotions(text)
for emotion, score in emotions:
    if score > 0.1:  # Only show significant emotions
        print(f"{emotion}: {score:.2f}")

print("\n6. Keyword Extraction")
print("-" * 50)
keyword_extractor = KeywordExtractor()
print("Keywords:")
keywords = keyword_extractor.extract_keywords(text, num_keywords=5)
for keyword, score in keywords:
    print(f"{keyword}: {score:.2f}")

print("\nKey Phrases:")
keyphrases = keyword_extractor.extract_keyphrases(text, num_phrases=3)
for phrase, score in keyphrases:
    print(f"{phrase}: {score:.2f}")