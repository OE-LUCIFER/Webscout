# 🎙️ Webscout Text-to-Speech (TTS) Providers

## Overview

Webscout's TTS Providers offer a versatile and powerful text-to-speech conversion library with support for multiple providers and advanced features.

## 🌟 Features

- **Multiple TTS Providers**: Support for various text-to-speech services
- **Concurrent Audio Generation**: Efficiently process long texts
- **Flexible Voice Selection**: Choose from a wide range of voices
- **Robust Error Handling**: Comprehensive logging and error management
- **Caching Mechanism**: Automatically cache generated audio files
- **Cross-Platform Compatibility**: Works seamlessly across different environments

## 📦 Supported TTS Providers

1. **ElevenlabsTTS**
2. **GesseritTTS**
3. **MurfAITTS**
4. **ParlerTTS**
5. **DeepgramTTS**
6. **StreamElementsTTS**
7. **VoicepodsTTS**

## 🚀 Installation

```bash
pip install webscout
```

## 💻 Basic Usage

```python
from webscout.Provider.TTS import ElevenlabsTTS

# Initialize the TTS provider
tts = ElevenlabsTTS()

# Generate speech from text
text = "Hello, this is a test of text-to-speech conversion."
audio_file = tts.tts(text, voice="Brian")

# Play the generated audio
tts.play_audio(audio_file)
```

## 🎛️ Advanced Configuration

### Voice Selection
Each TTS provider offers multiple voices:

```python
# List available voices
print(tts.all_voices.keys())

# Select a specific voice
audio_file = tts.tts(text, voice="Alice")
```

### Verbose Logging
Enable detailed logging for debugging:

```python
audio_file = tts.tts(text, verbose=True)
```

## 🔧 Provider-Specific Details

### ElevenlabsTTS
- Supports multiple English voices
- Multilingual text-to-speech

### GesseritTTS
- Offers unique voice characteristics
- Supports voice description customization

### MurfAITTS
- Provides specific voice models
- Supports custom voice descriptions

### ParlerTTS
- Uses Gradio Client for TTS generation
- Supports large and small model variants

### DeepgramTTS
- Multiple voice options
- Advanced voice selection

### StreamElementsTTS
- Wide range of international voices

### VoicepodsTTS
- Simple and straightforward API
- Efficient audio caching

## 🛡️ Error Handling

```python
try:
    audio_file = tts.tts(text)
except exceptions.FailedToGenerateResponseError as e:
    print(f"TTS generation failed: {e}")
```

## 🌐 Proxy Support

```python
# Use with proxy
tts = ElevenlabsTTS(proxies={
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
})
```