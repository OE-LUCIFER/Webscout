# ImgSys Provider 🎨

A powerful text-to-image generation provider that uses multiple AI models to create unique images from your prompts! 

## Features ✨

- Generate 2 unique images from random providers for each prompt
- Support for both synchronous and asynchronous operations
- Built-in retry logic with configurable attempts and delays
- Comprehensive error handling and input validation
- Easy image saving with custom names and directories
- Random user agent rotation for requests
- Proxy support for enhanced privacy
- Detailed documentation and examples

## Installation 🚀

The ImgSys provider is part of the Webscout package. You can install it using pip:

```bash
pip install webscout
```

## Usage Examples 📝

### Synchronous Usage

```python
from webscout import ImgSys

# Initialize the provider
provider = ImgSys()

# Generate images
images = provider.generate("A cool cyberpunk city at night")

# Save the images
provider.save(images, dir="my_images")
```

### Asynchronous Usage

```python
import asyncio
from webscout import AsyncImgSys

async def main():
    # Initialize the provider
    provider = AsyncImgSys()
    
    # Generate images
    images = await provider.generate("A cool cyberpunk city at night")
    
    # Save the images
    await provider.save(images, dir="my_images")

# Run the async function
asyncio.run(main())
```

### Advanced Usage

```python
from webscout import ImgSys

# Initialize with custom settings
provider = ImgSys(
    timeout=30,  # Custom timeout in seconds
    proxies={    # Optional proxy configuration
        "http": "http://proxy:8080",
        "https": "https://proxy:8080"
    }
)

# Generate images with custom retry settings
images = provider.generate(
    prompt="A majestic dragon in a fantasy landscape",
    max_retries=5,    # More retry attempts
    retry_delay=10    # Longer delay between retries
)

# Save with custom naming
provider.save(
    images,
    name="dragon_art",
    dir="fantasy_images",
    filenames_prefix="fantasy_"
)
```

## API Reference 📚

### ImgSys Class

#### Constructor

```python
def __init__(
    self,
    timeout: int = 60,
    proxies: Optional[dict] = None
)
```

Parameters:
- `timeout` (int): HTTP request timeout in seconds (default: 60)
- `proxies` (dict, optional): Proxy configuration for requests

#### Methods

##### generate()

```python
def generate(
    self,
    prompt: str,
    max_retries: int = 3,
    retry_delay: int = 5
) -> List[bytes]
```

Generate images from a text prompt.

Parameters:
- `prompt` (str): Your image description
- `max_retries` (int): Max retry attempts if something fails (default: 3)
- `retry_delay` (int): Seconds to wait between retries (default: 5)

Returns:
- `List[bytes]`: Generated images as bytes

##### save()

```python
def save(
    self,
    response: List[bytes],
    name: Optional[str] = None,
    dir: Optional[Union[str, Path]] = None,
    filenames_prefix: str = ""
) -> List[str]
```

Save generated images to disk.

Parameters:
- `response` (List[bytes]): Generated images
- `name` (str, optional): Custom name for images
- `dir` (Union[str, Path], optional): Save directory (default: current directory)
- `filenames_prefix` (str): Prefix for image filenames

Returns:
- `List[str]`: Paths to saved images

### AsyncImgSys Class

The `AsyncImgSys` class provides the same functionality as `ImgSys` but with async/await support. All methods are prefixed with `async` and should be called with `await`.

## Error Handling 🛡️

The provider includes comprehensive error handling:

- Input validation for empty prompts
- Retry logic for failed API calls
- Proper exception handling for network issues
- Graceful handling of API response errors

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📄

This provider is part of the Webscout package and is licensed under the same terms. 