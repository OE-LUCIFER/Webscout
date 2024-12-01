# 🎨 BlackboxAIImager - Fire AI Art Generator! 🔥

Yo fam! Welcome to BlackboxAIImager - your go-to provider for creating some absolutely fire AI art! 🎨 

## 🚀 Features

- Both sync and async support for maximum flexibility 💪
- Fire error handling for smooth operation 🛡️
- Optional logging with cyberpunk vibes 🌟
- Dynamic user agents for stealth mode 🥷
- Proxy support for extra privacy 🔒
- Customizable timeouts ⚙️
- Smart retry mechanism 🔄

## 💫 Installation

```bash
pip install webscout  # All you need fam! 🔥
```

## 🎯 Usage

### 🔥 Sync Way (BlackboxAIImager)

```python
from webscout import BlackboxAIImager

# Initialize with fire logging! 🚀
imager = BlackboxAIImager(logging=True)

# Generate a single image
images = imager.generate("Epic dragon breathing fire")
paths = imager.save(images)
print(paths)  # ['epic_dragon_0.jpg']

# Generate multiple images
images = imager.generate("Cyberpunk city at night", amount=3)
paths = imager.save(images)
print(paths)  # ['cyberpunk_city_0.jpg', 'cyberpunk_city_1.jpg', 'cyberpunk_city_2.jpg']

# Custom retry settings
images = imager.generate(
    "Beautiful sunset",
    max_retries=5,
    retry_delay=3
)
paths = imager.save(images)

# Stealth mode (no logging)
quiet_imager = BlackboxAIImager(logging=False)
images = quiet_imager.generate("Secret art")
paths = quiet_imager.save(images)
```

### ⚡ Async Way (AsyncBlackboxAIImager)

```python
from webscout import AsyncBlackboxAIImager
import asyncio

async def generate_art():
    # Initialize with fire logging! 🚀
    imager = AsyncBlackboxAIImager(logging=True)
    
    # Generate multiple images
    images = await imager.generate("Epic dragon breathing fire", amount=2)
    paths = await imager.save(images)
    print(paths)  # ['epic_dragon_0.jpg', 'epic_dragon_1.jpg']

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
imager = BlackboxAIImager(
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

## ⚡ Error Handling

We got your back with proper error handling:

```python
try:
    images = imager.generate("Cool art")
    paths = imager.save(images)
except RequestException as e:
    print("Connection issues! Check your internet! 🌐")
except Exception as e:
    print(f"Something went wrong fam: {e} 😢")
```

## 🔒 Security Tips

- Use proxies for extra privacy 🛡️
- Enable stealth mode (logging=False) for sensitive ops 🤫
- Don't expose sensitive info in prompts 🔐

Made with 💖 by the HelpingAI Team! Keep it real fam! 🔥👑
