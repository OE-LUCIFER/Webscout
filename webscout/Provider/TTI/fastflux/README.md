# 🎨 FastFlux Image Generator

Generate amazing images with FastFlux's AI art generator! 🚀

## 🌟 Features

- Fast and reliable image generation
- Both sync and async implementations
- Smart retry mechanism
- Multiple model options
- Different aspect ratios
- Proxy support
- Custom timeouts
- Easy-to-use interface

## 📦 Installation

```bash
pip install webscout
```

## 🚀 Quick Start

### Sync Usage

```python
from webscout import FastFluxImager

# Initialize the provider
provider = FastFluxImager()

# Generate a single image
images = provider.generate("A beautiful sunset over mountains")
paths = provider.save(images)

# Generate multiple images with parameters
images = provider.generate(
    prompt="Epic dragon breathing fire",
    amount=3,
    model="flux_1_dev",
    size="16_9"
)
paths = provider.save(images, dir="dragon_pics")
```

### Async Usage

```python
from webscout import AsyncFastFluxImager
import asyncio

async def generate_images():
    provider = AsyncFastFluxImager()
    
    # Generate multiple images
    images = await provider.generate(
        "Epic dragon in cyberpunk city",
        amount=2,
        model="flux_1_schnell"
    )
    paths = await provider.save(images, dir="outputs")

# Run the async function
asyncio.run(generate_images())
```

## 🎨 Available Models

- `flux_1_schnell` - Fast generation model (default)
- `flux_1_dev` - Developer model with detailed outputs
- `sana_1_6b` - SANA 1.6B model for specialized images



## ⚙️ Configuration

```python
# Custom settings
provider = FastFluxImager(
    timeout=120,  # Longer timeout
    proxies={
        'http': 'http://proxy:8080',
        'https': 'http://proxy:8080'
    },
    logging=True  # Enable logging
)

# Advanced usage
images = provider.generate(
    prompt="A shiny red sports car",
    amount=3,
    model="flux_1_dev",
    size="16_9",
    is_public=False,
    max_retries=5,
    retry_delay=3
)
```

## 💾 Save Options

```python
# Save with custom options
paths = provider.save(
    images,
    name="sports_car",  # Custom name
    dir="my_images",    # Custom directory
    filenames_prefix="v1_"  # Add prefix
)
```

## 🛡️ Error Handling

```python
try:
    images = provider.generate("Cool art")
    paths = provider.save(images)
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Generation failed: {e}")
```

## 💡 Tips

1. Use clear, descriptive prompts
2. `flux_1_schnell` is faster but `flux_1_dev` gives better quality
3. Set longer timeouts for better quality models
4. Enable proxies for better reliability
5. Use retry mechanism for stability
6. Save images with meaningful names
