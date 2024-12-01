# 🎨 TalkaiImager - Fire AI Art Generator! 🔥

Yo fam! Welcome to TalkaiImager - your go-to provider for creating some absolutely fire AI art! 🎨 

## 🚀 Features

- Both sync and async support for maximum flexibility 💪
- Fire error handling for smooth operation 🛡️
- Optional logging with cyberpunk vibes 🌟
- Dynamic user agents for stealth mode 🥷
- Proxy support for extra privacy 🔒
- Customizable timeouts and retries ⚙️
- Smart retry mechanism 🔄

## 💫 Installation

```bash
pip install webscout  # All you need fam! 🔥
```

## 🎯 Usage

### 🔥 Sync Way (TalkaiImager)

```python
from webscout import TalkaiImager

# Initialize with fire logging! 🚀
imager = TalkaiImager(logging=True)

# Generate a single image
images = imager.generate("Epic dragon breathing fire")
paths = imager.save(images)
print(paths)  # ['epic_dragon_0.png']

# Generate multiple images with retries
images = imager.generate(
    "Cyberpunk city at night",
    amount=3,
    max_retries=5,
    retry_delay=3
)
paths = imager.save(images)
print(paths)  # ['cyberpunk_city_0.png', 'cyberpunk_city_1.png', 'cyberpunk_city_2.png']

# Stealth mode (no logging)
quiet_imager = TalkaiImager(logging=False)
images = quiet_imager.generate("Secret art")
paths = quiet_imager.save(images)
```

### ⚡ Async Way (AsyncTalkaiImager)

```python
from webscout import AsyncTalkaiImager
import asyncio

async def generate_art():
    # Initialize with fire logging! 🚀
    imager = AsyncTalkaiImager(logging=True)
    
    # Generate multiple images
    images = await imager.generate(
        "Epic dragon breathing fire",
        amount=2,
        max_retries=3,
        retry_delay=5
    )
    paths = await imager.save(images)
    print(paths)  # ['epic_dragon_0.png', 'epic_dragon_1.png']

    # Custom save location
    images = await imager.generate("Cool art")
    paths = await imager.save(images, dir="my_art", filenames_prefix="fire_")

# Run it!
asyncio.run(generate_art())
```

### 🛠️ Advanced Usage

```python
# With proxy and custom timeout
imager = TalkaiImager(
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
    max_retries=5,
    retry_delay=3
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
except exceptions.APIConnectionError as e:
    print("Connection issues! Check your internet! 🌐")
except exceptions.InvalidResponseError as e:
    print("Invalid response from API! 🚫")
except exceptions.FailedToGenerateResponseError as e:
    print("Failed to generate image! 😢")
except Exception as e:
    print(f"Something went wrong fam: {e} 😢")
```

## 🔒 Security Tips

- Use proxies for extra privacy 🛡️
- Enable stealth mode (logging=False) for sensitive ops 🤫
- Don't expose sensitive info in prompts 🔐
- Use custom timeouts for stability 🕒

## 🎛️ Parameters Guide

- `amount`: Number of images to generate (default: 1)
- `max_retries`: Number of retry attempts (default: 3)
- `retry_delay`: Seconds between retries (default: 5)
- `timeout`: Request timeout in seconds (default: 60)

Made with 💖 by the HelpingAI Team! Keep it real fam! 🔥👑
