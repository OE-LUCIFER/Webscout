# 🥷 NinjaImager - Fire AI Art Generator! 🔥

Yo fam! Welcome to NinjaImager - your go-to provider for creating some absolutely fire AI art! 🎨 

## 🚀 Features

- Multiple fire models (stable-diffusion, flux-dev) 🎯
- Both sync and async support for maximum flexibility 💪
- Fire error handling for smooth operation 🛡️
- Optional logging with cyberpunk vibes 🌟
- Dynamic user agents for stealth mode 🥷
- Proxy support for extra privacy 🔒
- Customizable timeouts ⏱️

## 💫 Installation

```bash
pip install webscout  # All you need fam! 🔥
```

## 🎯 Usage

### 🔥 Sync Way (NinjaImager)

```python
from webscout import NinjaImager

# Initialize with fire logging! 🚀
imager = NinjaImager(logging=True)

# Generate a single image
images = imager.generate("Epic dragon breathing fire")
paths = imager.save(images)
print(paths)  # ['epic_dragon_0.png']

# Generate multiple images
images = imager.generate("Cyberpunk city at night", amount=3)
paths = imager.save(images)
print(paths)  # ['cyberpunk_city_0.png', 'cyberpunk_city_1.png', 'cyberpunk_city_2.png']

# Use different model
images = imager.generate("Beautiful sunset", model="stable-diffusion")
paths = imager.save(images)

# Stealth mode (no logging)
quiet_imager = NinjaImager(logging=False)
images = quiet_imager.generate("Secret art")
paths = quiet_imager.save(images)
```

### ⚡ Async Way (AsyncNinjaImager)

```python
from webscout import AsyncNinjaImager
import asyncio

async def generate_art():
    # Initialize with fire logging! 🚀
    imager = AsyncNinjaImager(logging=True)
    
    # Generate multiple images
    images = await imager.generate("Epic dragon breathing fire", amount=2)
    paths = await imager.save(images)
    print(paths)  # ['epic_dragon_0.png', 'epic_dragon_1.png']

    # Use different model
    images = await imager.generate("Beautiful sunset", model="stable-diffusion")
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
imager = NinjaImager(
    timeout=120,
    proxies={
        'http': 'http://10.10.10.1:8000',
        'https': 'http://10.10.10.1:8000'
    },
    logging=True
)

# Custom save options
images = imager.generate("Cool art")
paths = imager.save(
    images,
    name="masterpiece",
    dir="my_art_folder",
    filenames_prefix="fire_"
)
```

## 🎨 Available Models

- `flux-dev` (default): Latest and most fire model! 🔥
- `stable-diffusion`: Classic stable diffusion model 🎯

## ⚡ Error Handling

We got your back with proper error handling:

```python
try:
    images = imager.generate("Cool art")
    paths = imager.save(images)
except exceptions.ModelNotFoundError:
    print("Oops! Model not found fam! 😢")
except exceptions.APIConnectionError:
    print("Connection issues! Check your internet! 🌐")
except exceptions.InvalidResponseError:
    print("Got a weird response from the API! 🤔")
except exceptions.FailedToGenerateResponseError:
    print("Couldn't generate that image fam! 😢")
except exceptions.FailedToSaveImageError:
    print("Saving failed! Check your permissions! 💾")
```

## 🔒 Security Tips

- Keep your API keys safe! 🔐
- Use proxies for extra privacy 🛡️
- Don't expose sensitive info in prompts 🤫

Made with 💖 by the HelpingAI Team! Keep it real fam! 🔥👑
