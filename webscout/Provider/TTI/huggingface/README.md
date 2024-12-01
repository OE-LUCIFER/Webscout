# 🔥 HuggingFace Image Providers

Your go-to solution for generating fire images with HuggingFace's models! Both sync and async support! 🚀

## 🌟 Features

- 🎨 Support for all HuggingFace image models
- ⚡ Both sync and async implementations
- 🔄 Smart retry mechanism
- 🌐 Proxy support
- 📝 Comprehensive logging
- 🎯 Type hints
- 🚀 Easy to use

## 📦 Installation

```bash
pip install webscout
```

## 🚀 Quick Start

### Sync Usage

```python
from webscout import HFimager

# Initialize with your API key
provider = HFimager(api_token="your-hf-token")

# Generate a single image
images = provider.generate("A shiny red sports car")
paths = provider.save(images)

# Generate multiple images with parameters
images = provider.generate(
    prompt="Epic dragon in cyberpunk city",
    amount=3,
    model="runwayml/stable-diffusion-v1-5",
    guidance_scale=7.5,
    negative_prompt="blurry, bad quality",
    num_inference_steps=50,
    width=768,
    height=768
)
paths = provider.save(images, name="dragon", dir="outputs")
```

### Async Usage

```python
from webscout import AsyncHFimager
import asyncio

async def example():
    # Initialize with your API key
    provider = AsyncHFimager(api_token="your-hf-token")
    
    # Generate a single image
    images = await provider.generate("A shiny red sports car")
    paths = await provider.save(images)
    
    # Generate multiple images with parameters
    images = await provider.generate(
        prompt="Epic dragon in cyberpunk city",
        amount=3,
        model="runwayml/stable-diffusion-v1-5",
        guidance_scale=7.5,
        negative_prompt="blurry, bad quality",
        num_inference_steps=50,
        width=768,
        height=768
    )
    paths = await provider.save(images, name="dragon", dir="outputs")

# Run the example
asyncio.run(example())
```

## 🎨 Supported Models

- `stabilityai/stable-diffusion-xl-base-1.0` (default)
- `runwayml/stable-diffusion-v1-5`
- `CompVis/stable-diffusion-v1-4`
- `stabilityai/sdxl-turbo`
- And many more! 🎉

## ⚙️ Configuration Options

- `api_token`: Your HuggingFace API token
- `timeout`: Request timeout in seconds
- `proxies`: Proxy settings for requests

## 🎯 Generation Parameters

- `prompt`: Your image description
- `amount`: Number of images to generate
- `model`: Which model to use
- `guidance_scale`: Control how much to follow your prompt
- `negative_prompt`: What you don't want in the image
- `num_inference_steps`: More steps = better quality but slower
- `width`: Image width
- `height`: Image height
- `scheduler`: Which scheduler to use
- `seed`: Random seed for reproducibility

## 💾 Save Options

- `name`: Custom name for your images
- `dir`: Where to save your images
- `filenames_prefix`: Add prefix to filenames

## 🔥 Made with Love by HelpingAI

