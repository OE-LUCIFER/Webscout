# PollinationsAI Provider 🎨

A powerful text-to-image generation provider using Pollinations.ai! Generate stunning images with various styles and models. Supports both synchronous and asynchronous operations! 🚀

## Features 💫

- Multiple AI models for different styles 🎭
- Both sync and async support ⚡
- Built-in retry logic and error handling 🛡️
- Easy-to-use interface 🎯
- Beautiful logging with LitLogger 📝
- Random user agents with LitAgent 🔄

## Installation 📦

```bash
pip install webscout
```

## Quick Start 🚀

### Synchronous Usage

```python
from webscout import PollinationsAI

# Create provider
provider = PollinationsAI()

# Generate a single image
images = provider.generate("A cool cyberpunk city at night")
provider.save(images, dir="my_images")

# Generate multiple images with settings
images = provider.generate(
    prompt="A majestic dragon",
    amount=3,
    width=1024,
    height=1024,
    model="flux-3d"  # Use 3D style
)
provider.save(images, dir="dragon_pics")
```

### Asynchronous Usage

```python
import asyncio
from webscout import AsyncPollinationsAI

async def main():
    # Create provider
    provider = AsyncPollinationsAI()
    
    # Generate images
    images = await provider.generate(
        prompt="A beautiful sunset",
        amount=2,
        model="flux-realism"  # Use realistic style
    )
    
    # Save images
    paths = await provider.save(images, dir="sunset_pics")
    print(f"Saved images to: {paths}")

# Run async code
asyncio.run(main())
```

## Available Models 🎭

| Model | Description | Best For |
|-------|-------------|----------|
| `flux` | Default model | General purpose |
| `flux-realism` | Enhanced realism | Photos, portraits |
| `flux-cablyai` | CablyAI style | Artistic renders |
| `flux-anime` | Anime/manga style | Anime art |
| `flux-3d` | 3D-style renders | 3D scenes |
| `any-dark` | Dark/gothic style | Dark themes |
| `flux-pro` | Professional quality | High-quality art |
| `turbo` | Fast generation | Quick results |

## Advanced Usage 🔧

### Different Models for Different Styles

```python
# Anime style
anime_pics = provider.generate(
    prompt="Cute anime character",
    model="flux-anime"
)

# Realistic style
real_pics = provider.generate(
    prompt="Professional portrait",
    model="flux-realism"
)

# Quick generation
quick_pics = provider.generate(
    prompt="Quick concept art",
    model="turbo"
)
```

### Custom Settings

```python
# Custom timeout and proxies
provider = PollinationsAI(
    timeout=30,  # 30 seconds timeout
    proxies={
        "http": "http://proxy:8080"
    }
)

# Generate high-res images
images = provider.generate(
    prompt="Ultra detailed landscape",
    width=1920,
    height=1080,
    model="flux-pro"
)
```

## Error Handling 🛡️

The provider includes built-in retry logic and error handling:

```python
try:
    images = provider.generate(
        prompt="Test image",
        max_retries=3,  # Retry 3 times
        retry_delay=5   # Wait 5 seconds between retries
    )
except Exception as e:
    print(f"Generation failed: {e}")
```

## Contributing 🤝

Feel free to contribute! Check out our issues or submit PRs.

Made with 💖 by the HelpingAI Team
