# FreeAI Image Provider 🎨

Generate amazing images with our FreeAI provider! Access to powerful models like DALL-E 3 and Flux series! 🚀

## Features 💫
- Both sync and async support ⚡
- 7 powerful models to choose from 🎭
- Smart retry mechanism 🔄
- Custom image sizes 📐
- Save with custom names 💾
- Fire logging with cyberpunk theme 🌟
- Proxy support for stealth mode 🕵️‍♂️

## Quick Start 🚀

### Installation 📦
```bash
pip install webscout
```

### Basic Usage 💫

```python
# Sync way
from webscout import FreeAIImager

provider = FreeAIImager()
images = provider.generate("Epic dragon")
paths = provider.save(images)

# Async way
from webscout import AsyncFreeAIImager
import asyncio

async def generate():
    provider = AsyncFreeAIImager()
    images = await provider.generate("Cool art")
    paths = await provider.save(images)

asyncio.run(generate())
```

## Available Models 🎭

| Model | Description | Best For |
|-------|-------------|----------|
| `dall-e-3` | Latest DALL-E model (Default) | High quality general purpose |
| `Flux Pro Ultra` | Premium Flux model | Professional quality |
| `Flux Pro` | Standard Pro model | High quality images |
| `Flux Pro Ultra Raw` | Unprocessed Ultra output | Raw creative control |
| `Flux Schnell` | Fast generation model | Quick results |
| `Flux Realism` | Photorealistic model | Realistic images |
| `grok-2-aurora` | Aurora enhancement | Artistic flair |

## Advanced Usage 🔧

### Custom Settings
```python
provider = FreeAIImager(
    model="Flux Pro Ultra",
    timeout=120,
    logging=True
)

images = provider.generate(
    prompt="Epic dragon",
    amount=2,
    size="1024x1024",
    quality="hd",
    style="vivid"
)
paths = provider.save(images, dir="dragons")
```

### Async with Error Handling ⚡
```python
async def generate_safely():
    provider = AsyncFreeAIImager()
    try:
        images = await provider.generate(
            prompt="Epic dragon",
            model="Flux Pro Ultra",
            amount=2
        )
        paths = await provider.save(images, dir="dragons")
        print(f"Saved to: {paths}")
    except Exception as e:
        print(f"Oops! Something went wrong: {e}")

asyncio.run(generate_safely())
```

## Tips & Tricks 💡

1. Use `Flux Realism` for photorealistic images
2. Use `Flux Pro Ultra` for highest quality
3. Use `Flux Schnell` for quick drafts
4. Set custom timeouts for large generations
5. Enable logging for detailed progress updates