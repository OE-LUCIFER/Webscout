# 🔥 Artbit Image Providers

Your go-to solution for generating fire images with Artbit.ai! Both sync and async support! 🚀

## 🌟 Features

- 🎨 Support for all Artbit models
- ⚡ Both sync and async implementations
- 🔄 Smart retry mechanism
- 🌐 Proxy support
- 📝 Optional logging
- 🎯 Type hints
- 🚀 Easy to use

## 📦 Installation

```bash
pip install webscout
```

## 🚀 Quick Start

### Sync Usage

```python
from webscout import ArtbitImager

# Initialize with logging
provider = ArtbitImager(logging=True)

# Generate a single image
images = provider.generate("A shiny red sports car")
paths = provider.save(images)

# Generate multiple images with parameters
images = provider.generate(
    prompt="Epic dragon in cyberpunk city",
    amount=3,
    caption_model="sdxl",
    selected_ratio="1024",
    negative_prompt="blurry, bad quality"
)
paths = provider.save(images, name="dragon", dir="outputs")
```

### Async Usage

```python
from webscout import AsyncArtbitImager
import asyncio

async def example():
    # Initialize with logging
    provider = AsyncArtbitImager(logging=True)
    
    # Generate a single image
    images = await provider.generate("A shiny red sports car")
    paths = await provider.save(images)
    
    # Generate multiple images with parameters
    images = await provider.generate(
        prompt="Epic dragon in cyberpunk city",
        amount=3,
        caption_model="sdxl",
        selected_ratio="1024",
        negative_prompt="blurry, bad quality"
    )
    paths = await provider.save(images, name="dragon", dir="outputs")

# Run the example
asyncio.run(example())
```

## 🎨 Supported Models

- `sdxl` (default) - Stable Diffusion XL
- `sd` - Stable Diffusion
- And more coming soon! 🎉

## ⚙️ Configuration Options

- `timeout`: Request timeout in seconds
- `proxies`: Proxy settings for requests
- `logging`: Enable/disable fire logging

## 🎯 Generation Parameters

- `prompt`: Your image description
- `amount`: Number of images to generate
- `caption_model`: Which model to use
- `selected_ratio`: Image size ratio
- `negative_prompt`: What you don't want in the image

## 💾 Save Options

- `name`: Custom name for your images
- `dir`: Where to save your images
- `filenames_prefix`: Add prefix to filenames

## 🔥 Made with Love by HelpingAI
