# AIArta Image Generator

Generate stunning AI art with AI Arta! 🎨 This package provides both synchronous and asynchronous interfaces to the AIArta image generation service.

## Features

- Generate high-quality images from text prompts
- 45+ artistic styles and models to choose from
- Customize image generation with various parameters
- Save images with automatic naming and organization
- Both synchronous and asynchronous implementations

## Installation

```bash
pip install webscout
```

## Usage

### Synchronous Usage

```python
from webscout import AIArtaImager

# Initialize the provider
provider = AIArtaImager()

# Generate a single image
images = provider.generate("A cool cyberpunk city at night")
paths = provider.save(images, dir="my_images")

# Generate multiple images with different settings
images = provider.generate(
    prompt="Epic dragon breathing fire",
    amount=2, 
    model="flux"
)
provider.save(images, dir="dragon_pics")
```

### Asynchronous Usage

```python
from webscout import AsyncAIArtaImager
import asyncio

async def generate_images():
    # Initialize with logging
    provider = AsyncAIArtaImager(logging=True)
    
    # Generate a single image
    images = await provider.generate("A beautiful sunset over mountains")
    paths = await provider.save(images)
    
    # Generate multiple images with parameters
    images = await provider.generate(
        prompt="Epic dragon in cyberpunk city",
        amount=2,
        model="fantasy_art",
        negative_prompt="ugly, deformed",
        guidance_scale=7,
        num_inference_steps=30
    )
    paths = await provider.save(images, name="dragon", dir="outputs")

# Run the async function
asyncio.run(generate_images())
```

## Available Models

The AIArta provider supports 45+ models, including:

- `flux` - General purpose model
- `fantasy_art` - Fantasy-style images
- `photographic` - Realistic photographic style
- `watercolor` - Watercolor painting style
- `low_poly` - Low-poly art style
- `anime_tattoo` - Anime-inspired tattoo designs
- `cinematic_art` - Movie-like cinematic images

See the full list in the `model_aliases` variable in the code.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | str | | Your image description |
| amount | int | 1 | Number of images to generate |
| model | str | "Flux" | Model to use for generation |
| negative_prompt | str | "blurry, deformed hands, ugly" | What to avoid in the image |
| guidance_scale | int | 7 | How closely to follow the prompt |
| num_inference_steps | int | 30 | More steps = better quality but slower |
| aspect_ratio | str | "1:1" | Image aspect ratio |

## Advanced Usage

### Custom Timeouts and Proxies

```python
# Synchronous with custom settings
provider = AIArtaImager(
    timeout=120,
    proxies={"http": "http://proxy:8080"},
    logging=True
)

# Asynchronous with custom settings
async_provider = AsyncAIArtaImager(
    timeout=120,
    proxies={"http": "http://proxy:8080"},
    logging=True
)
```

### Saving Images with Custom Naming

```python
# Generate images
images = provider.generate("Beautiful landscape")

# Save with custom name and directory
provider.save(
    images,
    name="landscape",
    dir="my_art_folder",
    filenames_prefix="vacation_"
)
```

## Authentication

The provider handles authentication automatically, storing and refreshing tokens as needed. No manual setup required!