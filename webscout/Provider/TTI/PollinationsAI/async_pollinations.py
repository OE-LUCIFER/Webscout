"""PollinationsAI Async Provider - Same fire, but async! ⚡

Examples:
    >>> from webscout import AsyncPollinationsAI
    >>> import asyncio
    >>> 
    >>> async def main():
    ...     provider = AsyncPollinationsAI()
    ...     # Generate a single image
    ...     images = await provider.generate("A cool cyberpunk city at night")
    ...     paths = await provider.save(images, dir="my_images")
    ...     print(f"Saved images to: {paths}")
    ... 
    >>> asyncio.run(main())
"""

import aiohttp
import asyncio
import os
import time
from typing import List, Optional, Union
from string import punctuation
from random import choice
from pathlib import Path
from typing import AsyncGenerator

from webscout.AIbase import AsyncImageProvider
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent import LitAgent

# Set up logging with cyberpunk style! 🎨
logger = LitLogger(
    name="AsyncPollinationsAI",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK
)

# Get a fresh user agent! 🔄
agent = LitAgent()

class AsyncPollinationsAI(AsyncImageProvider):
    """Your async homie for generating fire images using pollinations.ai! 🎨

    This provider supports various models and image sizes, with built-in retry logic
    and error handling to make sure you get your images no cap! 💯

    Examples:
        >>> provider = AsyncPollinationsAI()
        >>> 
        >>> # Generate one image with default model
        >>> async def single_image():
        ...     image = await provider.generate("A futuristic city")
        ...     await provider.save(image, "city.jpg")
        >>> 
        >>> # Generate multiple with specific model
        >>> async def multiple_images():
        ...     images = await provider.generate(
        ...         prompt="Space station",
        ...         amount=3,
        ...         width=1024,
        ...         height=1024,
        ...         model="flux-3d"  # For 3D-style images
        ...     )
        ...     await provider.save(images, dir="space_pics")
        >>>
        >>> # Try different models
        >>> async def try_models():
        ...     # Anime style
        ...     anime = await provider.generate(
        ...         prompt="Anime character",
        ...         model="flux-anime"
        ...     )
        ...     # Realistic style
        ...     real = await provider.generate(
        ...         prompt="Portrait photo",
        ...         model="flux-realism"
        ...     )
        ...     # Fast generation
        ...     quick = await provider.generate(
        ...         prompt="Quick sketch",
        ...         model="turbo"
        ...     )

    Attributes:
        AVAILABLE_MODELS (list): Available models to use:
            - "flux": Default model, good for general use
            - "flux-realism": Enhanced realism
            - "flux-cablyai": CablyAI style
            - "flux-anime": Anime/manga style
            - "flux-3d": 3D-style renders
            - "any-dark": Dark/gothic style
            - "flux-pro": Professional quality
            - "turbo": Fast generation
        DEFAULT_MODEL (str): Default model to use ("flux")
    """

    AVAILABLE_MODELS = [
        "flux",
        "flux-realism",
        "flux-cablyai",
        "flux-anime",
        "flux-3d",
        "any-dark",
        "flux-pro",
        "turbo"
    ]
    DEFAULT_MODEL = "flux"

    def __init__(
        self, 
        timeout: int = 60, 
        proxies: Optional[dict] = None
    ):
        """Initialize your AsyncPollinationsAI provider with custom settings

        Examples:
            >>> provider = AsyncPollinationsAI(timeout=30)
            >>> provider = AsyncPollinationsAI(proxies={"http": "http://proxy:8080"})

        Args:
            timeout (int): HTTP request timeout in seconds (default: 60)
            proxies (dict, optional): Proxy configuration for requests
        """
        self.image_gen_endpoint = "https://image.pollinations.ai/prompt/{prompt}"
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": agent.random(),
        }

        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "jpeg"

    async def generate(
        self,
        prompt: str,
        amount: int = 1,
        additives: bool = True,
        width: int = 768,
        height: int = 768,
        model: str = DEFAULT_MODEL,
        max_retries: int = 3,
        retry_delay: int = 5,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> List[bytes]:
        """Generate some fire images from your prompt asynchronously! ⚡

        Examples:
            >>> provider = AsyncPollinationsAI()
            >>> async def example():
            ...     # Basic usage
            ...     images = await provider.generate("Cool art")
            ...     # Advanced usage
            ...     images = await provider.generate(
            ...         prompt="Epic dragon",
            ...         amount=3,
            ...         model="flux-3d"
            ...     )

        Args:
            prompt (str): Your image description
            amount (int): How many images you want (default: 1)
            additives (bool): Make each prompt unique for variety (default: True)
            width (int): Image width (default: 768)
            height (int): Image height (default: 768)
            model (str): Model to use - check AVAILABLE_MODELS (default: "flux")
            max_retries (int): Max retry attempts if something fails (default: 3)
            retry_delay (int): Seconds to wait between retries (default: 5)
            negative_prompt (str, optional): What you don't want in the image
            seed (int, optional): Seed for reproducible results

        Returns:
            List[bytes]: Your generated images as bytes

        Raises:
            ValueError: If the inputs ain't valid
            aiohttp.ClientError: If the API calls fail after retries
        """
        # Input validation
        if not prompt:
            raise ValueError("Yo fam, the prompt can't be empty! 🤔")
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Amount needs to be a positive number! 📈")
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model must be one of {self.AVAILABLE_MODELS}! 🎯")

        # Function to add random characters for variety
        def add_variety():
            return "" if not additives else "".join(choice(punctuation) for _ in range(5))

        self.prompt = prompt
        response = []
        
        # Build base URL with parameters
        base_params = {
            "width": width,
            "height": height,
            "model": model
        }
        
        if negative_prompt:
            base_params["negative"] = negative_prompt
        if seed is not None:
            base_params["seed"] = seed

        async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
            tasks = []
            for _ in range(amount):
                current_prompt = f"{prompt}{add_variety()}"
                params_str = "&".join(f"{k}={v}" for k, v in base_params.items())
                url = f"{self.image_gen_endpoint.format(prompt=current_prompt)}?{params_str}"
                
                logger.info(f"Queueing image {_ + 1}/{amount} generation... ⚡")
                tasks.append(self._generate_single(session, url, max_retries, retry_delay))
            
            response = await asyncio.gather(*tasks)
            logger.success(f"Successfully generated {amount} images! 🎨")

        return response

    async def _generate_single(
        self, 
        session: aiohttp.ClientSession, 
        url: str, 
        max_retries: int, 
        retry_delay: int
    ) -> bytes:
        """Helper method to generate a single image with retries"""
        for attempt in range(max_retries):
            try:
                async with session.get(url, proxy=self.proxies) as resp:
                    resp.raise_for_status()
                    return await resp.read()
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to generate image: {e} 😢")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds... 🔄")
                await asyncio.sleep(retry_delay)

    async def save(
        self,
        response: Union[AsyncGenerator[bytes, None], List[bytes]],
        name: Optional[str] = None,
        dir: Optional[Union[str, Path]] = None,
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire generated images asynchronously! 💾

        Examples:
            >>> provider = AsyncPollinationsAI()
            >>> async def example():
            ...     images = await provider.generate("Cool art")
            ...     # Save with default settings
            ...     paths = await provider.save(images)
            ...     # Save with custom name and directory
            ...     paths = await provider.save(
            ...         images,
            ...         name="my_art",
            ...         dir="my_images",
            ...         filenames_prefix="test_"
            ...     )

        Args:
            response (Union[AsyncGenerator[bytes, None], List[bytes]]): Your generated images
            name (Optional[str]): Custom name for your images
            dir (Optional[Union[str, Path]]): Where to save the images (default: current directory)
            filenames_prefix (str): Prefix for your image files

        Returns:
            List[str]: Paths to your saved images
        """
        save_dir = dir if dir else os.getcwd()
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            logger.info(f"Created directory: {save_dir} 📁")

        saved_paths = []
        timestamp = int(time.time())
        
        async def save_single_image(image_bytes: bytes, index: int) -> str:
            if name:
                filename = f"{filenames_prefix}{name}_{index}.{self.image_extension}"
            else:
                filename = f"{filenames_prefix}pollinations_{timestamp}_{index}.{self.image_extension}"
            
            filepath = os.path.join(save_dir, filename)
            
            # Write file using asyncio
            async with asyncio.Lock():
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
            
            logger.success(f"Saved image to: {filepath} 💾")
            return filepath

        # Handle both List[bytes] and AsyncGenerator
        if isinstance(response, list):
            image_list = response
        else:
            image_list = [chunk async for chunk in response]

        tasks = [save_single_image(img, i) for i, img in enumerate(image_list)]
        saved_paths = await asyncio.gather(*tasks)
        logger.success(f"Successfully saved all {len(saved_paths)} images! 🎉")
        return saved_paths


if __name__ == "__main__":
    # Example usage
    async def main():
        provider = AsyncPollinationsAI()
        try:
            images = await provider.generate(
                prompt="A cyberpunk city at night with neon lights",
                amount=2,
                width=1024,
                height=1024,
                model="sdxl"
            )
            paths = await provider.save(images, dir="generated_images")
            print(f"Successfully saved images to: {paths}")
        except Exception as e:
            print(f"Oops, something went wrong: {e}")

    asyncio.run(main())
