# 🔍 Webscout AI Search Providers

## Overview

Webscout's AI Search Providers offer powerful and flexible AI-powered search capabilities with support for multiple providers. These providers leverage advanced language models and search algorithms to deliver high-quality, context-aware responses.

## 🌟 Features

- **Multiple Search Providers**: Support for various AI search services
- **Streaming Responses**: Real-time streaming of AI-generated responses
- **Raw Response Format**: Access to raw response data when needed
- **Automatic Text Handling**: Smart response formatting and cleaning
- **Robust Error Handling**: Comprehensive error management
- **Cross-Platform Compatibility**: Works seamlessly across different environments

## 📦 Supported Search Providers

1. **DeepFind**
   - Advanced web-based AI search
   - Streaming response support
   - Clean response formatting

2. **Felo**
   - Powerful search interface
   - Real-time response streaming
   - Context-aware responses

3. **Isou**
   - Multiple model options
   - Scientific and general query support
   - References and citations included

4. **Genspark**
   - Fast and efficient search responses
   - Clean markdown link removal
   - Streamlined response parsing

## 🚀 Installation

```bash
pip install webscout
```

## 💻 Basic Usage

### DeepFind Example

```python
from webscout import DeepFind

# Initialize the search provider
ai = DeepFind()

# Basic search
response = ai.search("What is Python?")
print(response)  # Automatically formats the response

# Streaming search
for chunk in ai.search("Tell me about AI", stream=True):
    print(chunk, end="")  # Print response as it arrives

# Raw response format
for chunk in ai.search("Hello", stream=True, raw=True):
    print(chunk)  # {'text': 'response chunk'}
```

### Felo Example

```python
from webscout import Felo

# Initialize the search provider
ai = Felo()

# Basic search
response = ai.search("What is machine learning?")
print(response)

# Streaming search
for chunk in ai.search("Explain quantum computing", stream=True):
    print(chunk, end="")
```

### Isou Example

```python
from webscout import Isou

# Initialize with specific model
ai = Isou(model="siliconflow:deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")

# Get a response with scientific information
response = ai.search("Explain the double-slit experiment")
print(response)
```

### Genspark Example

```python
from webscout import Genspark

# Initialize Genspark
ai = Genspark()

# Basic search
response = ai.search("What are neural networks?")
print(response)

# Streaming search with clean output
for chunk in ai.search("Explain blockchain technology", stream=True):
    print(chunk, end="", flush=True)
```

## 🎛️ Advanced Configuration

### Timeout and Proxy Settings

```python
# Configure timeout
ai = DeepFind(timeout=60)  # 60 seconds timeout

# Use with proxy
proxies = {'http': 'http://proxy.com:8080'}
ai = Felo(proxies=proxies)

# Configure max tokens (for providers that support it)
ai = Genspark(max_tokens=800)
```

### Response Formats

```python
# Get raw response format
response = ai.search("Hello", stream=True, raw=True)
# Output: {'text': 'Hello'}, {'text': ' there!'}, etc.

# Get formatted text response
response = ai.search("Hello", stream=True)
# Output: Hello there!
```

## 🔧 Provider-Specific Details

### DeepFind
- Web-based AI search provider
- Automatic reference removal
- Clean response formatting
- Streaming support with progress tracking

### Felo
- Advanced search capabilities
- Real-time response streaming
- JSON-based response parsing
- Automatic text cleaning

### Isou
- Multiple model selection
- Scientific and general category support
- Citation and reference handling
- Deep and simple search modes

### Genspark
- Fast response generation
- Automatic markdown link removal
- JSON structure normalization
- Session-based API interactions

## 🛡️ Error Handling

```python
from webscout import exceptions

try:
    response = ai.search("Your query")
except exceptions.APIConnectionError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
```

## 📝 Response Handling

All providers include a `Response` class that automatically handles text formatting:

```python
# Response objects automatically convert to text
response = ai.search("What is AI?")
print(response)  # Prints formatted text

# Access raw text if needed
print(response.text)
```

## 🔒 Best Practices

1. **Use Streaming for Long Responses**
   ```python
   for chunk in ai.search("Long query", stream=True):
       print(chunk, end="", flush=True)
   ```

2. **Handle Errors Appropriately**
   ```python
   try:
       response = ai.search("Query")
   except exceptions.APIConnectionError:
       # Handle connection errors
       pass
   ```

3. **Choose the Right Provider for Your Use Case**
   - **DeepFind**: General purpose search
   - **Felo**: Fast streaming responses
   - **Isou**: Scientific or specialized queries
   - **Genspark**: Clean and efficient responses

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
