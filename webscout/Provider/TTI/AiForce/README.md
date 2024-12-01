# AiForce Provider 🔥

Yo fam! This is the AiForce provider for generating some fire images! Part of the HelpingAI squad! 👑

## Features 💪
- Both sync and async support ⚡
- 12 fire models to choose from 🎨
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
from webscout import AiForceimager

provider = AiForceimager()
images = provider.generate("Epic dragon")
paths = provider.save(images)

# Async way
from webscout import AsyncAiForceimager
import asyncio

async def generate():
    provider = AsyncAiForceimager()
    images = await provider.generate("Cool art")
    paths = await provider.save(images)

asyncio.run(generate())
```

## Available Models 🎭

| Model | Description | Best For |
|-------|-------------|----------|
| `Flux-1.1-Pro` | Latest pro model (Default) | High quality general purpose |
| `stable-diffusion-xl-lightning` | Fast SDXL model | Quick generations |
| `stable-diffusion-xl-base` | Base SDXL model | High quality base |
| `ideogram` | Artistic model | Creative artwork |
| `flux` | Standard model | General purpose |
| `flux-realism` | Photorealistic model | Realistic images |
| `flux-anime` | Anime style | Anime/manga art |
| `flux-3d` | 3D rendering | 3D objects/scenes |
| `flux-disney` | Disney style | Disney-like art |
| `flux-pixel` | Pixel art | Retro/game art |
| `flux-4o` | 4k output | High resolution |
| `any-dark` | Dark theme | Gothic/dark art |

## Advanced Examples 🔥

### Custom Settings 🛠️
```python
provider = AiForceimager(
    timeout=120,  # Longer timeout
    proxies={
        'http': 'http://proxy.example.com:8080'
    }
)
```

### Multiple Images with Custom Size 📸
```python
images = provider.generate(
    prompt="A shiny red sports car",
    amount=3,  # Generate 3 images
    model="flux-realism",  # Use realistic model
    width=1024,  # Custom width
    height=768,  # Custom height
    seed=42  # For reproducible results
)
```

### Custom Save Options 💾
```python
paths = provider.save(
    images,
    name="sports_car",  # Custom name
    dir="my_images",  # Custom directory
    filenames_prefix="v1_"  # Add prefix
)
```

### Async with Error Handling ⚡
```python
async def generate_safely():
    provider = AsyncAiForceimager()
    try:
        images = await provider.generate(
            prompt="Epic dragon",
            model="flux-3d",
            amount=2
        )
        paths = await provider.save(images, dir="dragons")
        print(f"Saved to: {paths}")
    except Exception as e:
        print(f"Oops! Something went wrong: {e}")

asyncio.run(generate_safely())
```

## Tips & Tricks 💡

1. Use `flux-realism` for photorealistic images
2. Use `flux-3d` for product renders
3. Use `flux-anime` for anime style art
4. Set custom timeouts for large images
5. Use proxies for better reliability
6. Add seed for reproducible results

## Error Handling 🛡️

The provider handles common errors:
- Network issues
- API timeouts
- Invalid inputs
- File saving errors

Example with retry:
```python
provider = AiForceimager()
try:
    images = provider.generate(
        "Epic scene",
        max_retries=5,  # More retries
        retry_delay=10  # Longer delay
    )
except Exception as e:
    print(f"Generation failed: {e}")
```

## Contributing 🤝

Pull up to the squad! We're always looking for improvements:
1. Fork it
2. Create your feature branch
3. Push your changes
4. Hit us with that pull request

Made with 💖 by the HelpingAI Team
