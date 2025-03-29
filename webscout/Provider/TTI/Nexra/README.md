# Nexra Provider 🔥

Yo fam! This is the Nexra provider for generating some fire images! Part of the HelpingAI squad! 👑

## Features 💪

- Standard & Prodia models ⚡
- 19+ fire models to choose from 🎨
- Smart retry mechanism 🔄
- Custom parameters support 🛠️
- Save with custom names 💾
- Fire logging with cyberpunk theme 🌟
- Proxy support for stealth mode 🕵️‍♂️

## Quick Start 🚀

### Installation 📦

```bash
pip install webscout
```

### Basic Usage 💫

```python
from webscout import NexraImager

# Basic usage
provider = NexraImager()
images = provider.generate("Epic dragon")
paths = provider.save(images)

# With custom model
provider = NexraImager()
images = provider.generate(
    prompt="Epic dragon",
    model="midjourney"
)
paths = provider.save(images)
```

## Available Models 🎭

### Standard Models 🌟

| Model | Description | Best For |
|-------|-------------|----------|
| `emi` | Eminent AI model | General purpose |
| `stablediffusion-1.5` | Classic SD model | Proven quality |
| `stablediffusion-2.1` | Improved SD model | Better quality |
| `sdxl-lora` | SDXL with LoRA | Custom styles |
| `dalle` | OpenAI's DALL-E | Clean images |
| `dalle2` | DALL-E 2 model | High quality |
| `dalle-mini` | Lightweight DALL-E | Quick generations |
| `flux` | Standard Flux | General purpose |
| `midjourney` | MJ style | Artistic images |

### Prodia Models 🚀

| Model | Description |
|-------|-------------|
| `dreamshaperXL10_alpha2` | Dreamlike creations |
| `dynavisionXL_0411` | Dynamic visuals |
| `juggernautXL_v45` | Powerful generations |
| `realismEngineSDXL_v10` | Photorealistic images |
| `sd_xl_base_1.0` | Base SDXL model |
| `animagineXLV3_v30` | Anime style art |
| `sd_xl_base_1.0_inpainting` | Inpainting specialist |
| `turbovisionXL_v431` | Fast generations |
| `devlishphotorealism_sdxl15` | Ultra-realistic |
| `realvisxlV40` | Reality-based art |

## Advanced Examples 🔥

### Custom Settings 🛠️

```python
provider = NexraImager(
    timeout=120,  # Longer timeout
    proxies={
        'http': 'http://proxy.example.com:8080'
    }
)
```

### Prodia Model with Custom Params 📸

```python
images = provider.generate(
    prompt="A shiny red sports car",
    model="realismEngineSDXL_v10.safetensors [af771c3f]",
    additional_params={
        "data": {
            "steps": 30,
            "cfg_scale": 8,
            "sampler": "DPM++ 2M Karras",
            "negative_prompt": "blurry, low quality"
        }
    }
)
```

### Custom Save Options 💾

```python
paths = provider.save(
    images,
    name="sports_car",  # Custom name
    dir="my_images",  # Custom directory
    filenames_prefix="v1_"  # Add prefix
)
```

### Error Handling 🛡️

```python
try:
    images = provider.generate(
        prompt="Epic scene",
        model="midjourney",
        max_retries=5,  # More retries
        retry_delay=10  # Longer delay
    )
    paths = provider.save(images, dir="scenes")
except Exception as e:
    print(f"Oops! Something went wrong: {e}")
```

## Tips & Tricks 💡

1. Use `midjourney` for artistic images
2. Use `realismEngineSDXL` for photorealistic shots
3. Use `animagineXLV3` for anime style
4. Adjust steps and cfg_scale for better quality
5. Use custom negative prompts
6. Set longer timeouts for complex generations

The provider handles common errors:

- Network issues
- JSON parsing errors
- API timeouts
- Invalid inputs
- File saving errors

## Contributing 🤝

Pull up to the squad! We're always looking for improvements:

1. Fork it
2. Create your feature branch
3. Push your changes
4. Hit us with that pull request

Made with 💖 by the HelpingAI Team
