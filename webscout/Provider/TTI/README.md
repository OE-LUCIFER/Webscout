# 🎨 WebScout Text-to-Image (TTI) Providers

Welcome to WebScout's Text-to-Image providers - your ultimate collection of AI art generators! 🚀

## 🌟 Available Providers

* **[AiForce](AiForce/README.md):** Advanced AI image generation with 12 specialized models including Flux-1.1-Pro, SDXL Lightning, and Ideogram, perfect for both quick generations and high-quality art
* **[Nexra](Nexra/README.md):** Next-gen image creation with 19+ models including MidJourney, DALL-E, and specialized SDXL variants for every use case from anime to photorealism
* **[BlackboxAI](blackbox/README.md):** High-performance image generation with advanced retry mechanisms, perfect for reliable and consistent results
* **[DeepInfra](deepinfra/README.md):** Powerful image generation using FLUX-1-schnell and other cutting-edge models, optimized for high-quality outputs
* **[TalkAI](talkai/README.md):** Fast and reliable image generation with comprehensive error handling and dynamic user agent support
* **[ImgNinza](imgninza/README.md):** Ninja-fast image generation with cyberpunk-themed logging and stealth capabilities
* **[PollinationsAI](PollinationsAI/README.md):** Nature-inspired AI art generation with specialized models for organic and natural imagery
* **[Artbit](artbit/README.md):** Bit-perfect AI art creation with precise control over generation parameters
* **[HuggingFace](huggingface/README.md):** Direct integration with HuggingFace's powerful models for research-grade image generation

## 🚀 Features

All providers come with these fire features:

### 🛠️ Core Features
- Both sync and async implementations
- Comprehensive error handling
- Optional logging with cyberpunk theme
- Dynamic user agent generation
- Proxy support
- Customizable timeouts
- Smart retry mechanisms

### 💫 Developer Experience
- Consistent API across all providers
- Detailed documentation with examples
- Type hints for better IDE support
- Comprehensive error messages
- Easy-to-use interface

### 🔒 Security Features
- Proxy support for privacy
- Configurable timeouts
- Safe error handling
- Optional verbose logging
- Dynamic user agent rotation

## 🎯 Usage Example

```python
# Sync way
from webscout.Provider.TTI import BlackboxAIImager

imager = BlackboxAIImager(logging=True)
images = imager.generate("Epic dragon breathing fire", amount=2)
paths = imager.save(images)

# Async way
from webscout.Provider.TTI import AsyncDeepInfraImager
import asyncio

async def generate_art():
    imager = AsyncDeepInfraImager(logging=True)
    images = await imager.generate("Cyberpunk city at night")
    paths = await imager.save(images)

asyncio.run(generate_art())
```

## 🔧 Installation

```bash
pip install webscout
```

## 📚 Common Interface

All providers implement these base classes:
- `ImageProvider` for sync operations
- `AsyncImageProvider` for async operations

### 🎨 Common Methods

```python
def generate(
    self,
    prompt: str,           # Your creative prompt
    amount: int = 1,       # Number of images
    max_retries: int = 3,  # Max retry attempts
    retry_delay: int = 5   # Delay between retries
) -> List[bytes]:         # Returns image data
    ...

def save(
    self,
    response: List[bytes], # Image data
    name: str = None,      # Base filename
    dir: str = os.getcwd(),# Save directory
    prefix: str = ""       # Filename prefix
) -> List[str]:           # Returns saved paths
    ...
```

## 🛡️ Error Handling

All providers use these standard exceptions:
- `APIConnectionError`: Network/connection issues
- `InvalidResponseError`: Invalid API responses
- `FailedToGenerateResponseError`: Generation failures

## 🎛️ Configuration

Common configuration options:
```python
imager = Provider(
    timeout=60,      # Request timeout
    proxies={},      # Proxy settings
    logging=True     # Enable logging
)
```

## 🔐 Security Best Practices

1. Use proxies for privacy
2. Enable stealth mode when needed
3. Don't expose API keys
4. Use custom timeouts
5. Handle errors gracefully

## 🚀 Performance Tips

1. Use async for multiple images
2. Enable retry mechanisms
3. Configure appropriate timeouts
4. Use chunked downloads
5. Implement parallel saving

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Follow the provider template
4. Add comprehensive tests
5. Submit a pull request

Made with 💖 by the HelpingAI Team! Keep it real fam! 🔥👑
