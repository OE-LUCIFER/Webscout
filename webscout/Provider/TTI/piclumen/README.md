# 🎨 PiclumenImager - Professional AI Image Generation

Welcome to PiclumenImager - a powerful provider for creating high-quality AI-generated images.

## ✨ Features

- Professional-grade image generation with photorealistic outputs
- Synchronous and asynchronous operation support
- Robust error handling and retry mechanisms
- Dynamic user agent management
- Configurable proxy support
- Customizable timeouts and retry settings
- Smart error recovery system

## 📦 Installation

```bash
pip install webscout
```

## 📘 Usage Guide

### Synchronous Usage (PiclumenImager)

```python
from webscout import PiclumenImager

# Basic initialization
imager = PiclumenImager()

# Generate a single image
images = imager.generate("Dragon in flight over mountain peaks")
paths = imager.save(images)
print(f"Image saved to: {paths[0]}")

# Generate multiple images with retry configuration
images = imager.generate(
    "Bioluminescent deep sea creature in natural habitat",
    amount=3,
    max_retries=5,
    retry_delay=3
)
paths = imager.save(images)
print(f"Images saved to: {paths}")

# Configure with custom settings
custom_imager = PiclumenImager(timeout=180)
images = custom_imager.generate("Abstract architectural concept")
paths = custom_imager.save(images)
```

### Asynchronous Usage (AsyncPiclumenImager)

```python
from webscout import AsyncPiclumenImager
import asyncio

async def generate_images():
    imager = AsyncPiclumenImager()
    
    # Generate multiple images concurrently
    images = await imager.generate(
        "Architectural visualization of modern building",
        amount=2,
        max_retries=3,
        retry_delay=5
    )
    paths = await imager.save(images)
    print(f"Generated images: {paths}")

    # Custom save configuration
    images = await imager.generate("Modern art composition")
    paths = await imager.save(
        images, 
        dir="artwork",
        filenames_prefix="modern_"
    )

# Execute the async function
asyncio.run(generate_images())
```

### Advanced Configuration

```python
# Initialize with proxy and extended timeout
imager = PiclumenImager(
    timeout=180,
    proxies={
        'http': 'http://proxy.example.com:8000',
        'https': 'http://proxy.example.com:8000'
    }
)

# Advanced image generation with custom settings
images = imager.generate(
    "Professional product photography of luxury watch",
    max_retries=5,
    retry_delay=3
)
paths = imager.save(
    images,
    name="product_photo",
    dir="product_images",
    filenames_prefix="watch_"
)
```

## ⚡ Error Handling

Comprehensive error handling implementation:

```python
try:
    images = imager.generate("Product photography")
    paths = imager.save(images)
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
except ValueError as e:
    print(f"Invalid parameter: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 🎯 Image Quality Specializations

PiclumenImager excels in generating:

- Photorealistic images with accurate lighting and shadows
- Detailed textures and material representations
- Complex underwater and nature scenes
- Architectural and product visualizations
- Macro photography simulations

## 🔒 Security Considerations

- Implement proxy configuration for enhanced privacy
- Use secure network connections
- Follow API rate limiting guidelines
- Handle sensitive data appropriately
- Monitor and log API usage when needed

## 💡 Optimization Tips

For optimal results:

1. Provide detailed, specific prompts
2. Include lighting and environment details
3. Reference professional photography styles
4. Specify desired color schemes
5. Adjust timeouts for complex generations
6. Use appropriate retry settings for reliability

## 📚 Technical Notes

- Default timeout: 120 seconds
- Maximum retries: 3 (configurable)
- Supports JPEG image format
- Implements automatic error recovery
- Handles concurrent image generation
- Supports both sync and async workflows
