# 🎨 DeepInfraImager - Fire AI Art Generator! 🔥

Yo fam! Welcome to DeepInfraImager - your go-to provider for creating some absolutely fire AI art! 🎨 

## 🚀 Features

- Both sync and async support for maximum flexibility 💪
- Multiple model support including FLUX-1-schnell 🤖
- Fire error handling for smooth operation 🛡️
- Optional logging with cyberpunk vibes 🌟
- Dynamic user agents for stealth mode 🥷
- Proxy support for extra privacy 🔒
- Customizable timeouts and retries ⚙️
- Adjustable image generation parameters 🎛️

## 💫 Installation

```bash
pip install webscout  # All you need fam! 🔥
```

## 🎯 Usage

### 🔥 Sync Way (DeepInfraImager)

```python
from webscout import DeepInfraImager

# Initialize with fire logging! 🚀
imager = DeepInfraImager(logging=True)

# Generate a single image
images = imager.generate("Epic dragon breathing fire")
paths = imager.save(images)
print(paths)  # ['epic_dragon_0.png']

# Generate multiple images with custom settings
images = imager.generate(
    "Cyberpunk city at night",
    amount=3,
    width=1024,
    height=1024,
    num_inference_steps=25,
    guidance_scale=7.5
)
paths = imager.save(images)
print(paths)  # ['cyberpunk_city_0.png', 'cyberpunk_city_1.png', 'cyberpunk_city_2.png']

# Use a different model
custom_imager = DeepInfraImager(
    model="black-forest-labs/FLUX-1-schnell",
    logging=True
)
images = custom_imager.generate("Beautiful sunset")
paths = custom_imager.save(images)

# Stealth mode (no logging)
quiet_imager = DeepInfraImager(logging=False)
images = quiet_imager.generate("Secret art")
paths = quiet_imager.save(images)
```

### ⚡ Async Way (AsyncDeepInfraImager)

```python
from webscout import AsyncDeepInfraImager
import asyncio

async def generate_art():
    # Initialize with fire logging! 🚀
    imager = AsyncDeepInfraImager(logging=True)
    
    # Generate multiple images
    images = await imager.generate(
        "Epic dragon breathing fire",
        amount=2,
        width=1024,
        height=1024
    )
    paths = await imager.save(images)
    print(paths)  # ['epic_dragon_0.png', 'epic_dragon_1.png']

    # Custom retry settings
    images = await imager.generate(
        "Beautiful sunset",
        max_retries=5,
        retry_delay=3
    )
    paths = await imager.save(images)
    
    # Custom save location
    images = await imager.generate("Cool art")
    paths = await imager.save(images, dir="my_art", filenames_prefix="fire_")

# Run it!
asyncio.run(generate_art())
```

### 🛠️ Advanced Usage

```python
# With proxy and custom timeout
imager = DeepInfraImager(
    model="black-forest-labs/FLUX-1-schnell",
    timeout=120,
    proxies={
        'http': 'http://10.10.10.1:8000',
        'https': 'http://10.10.10.1:8000'
    },
    logging=True
)

# Custom save options
images = imager.generate(
    "Cool art",
    width=1024,
    height=1024,
    num_inference_steps=30,
    guidance_scale=8.0,
    seed=42  # For reproducible results
)
paths = imager.save(
    images,
    name="masterpiece",
    dir="my_art_folder",
    filenames_prefix="fire_"
)
```

## ⚡ Error Handling

We got your back with proper error handling:

```python
try:
    images = imager.generate("Cool art")
    paths = imager.save(images)
except Exception as e:
    print(f"Something went wrong fam: {e} 😢")
```

## 🔒 Security Tips

- Use proxies for extra privacy 🛡️
- Enable stealth mode (logging=False) for sensitive ops 🤫
- Don't expose sensitive info in prompts 🔐
- Use custom timeouts for stability 🕒

## 🎛️ Parameters Guide

- `num_inference_steps`: Higher = better quality but slower (default: 25)
- `guidance_scale`: Higher = more prompt adherence (default: 7.5)
- `width/height`: Image dimensions (default: 1024x1024)
- `seed`: Set for reproducible results
- `additives`: Adds random chars to make each prompt unique

Made with 💖 by the HelpingAI Team! Keep it real fam! 🔥👑
