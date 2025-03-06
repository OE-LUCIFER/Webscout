"""PiclumenImager Async Provider - Same fire, but async! ⚡

Examples:
    >>> from webscout import AsyncPiclumenImager
    >>> import asyncio
    >>> 
    >>> async def main():
    ...     provider = AsyncPiclumenImager()
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
import json
from typing import List, Optional, Union, AsyncGenerator
from datetime import datetime
from pathlib import Path

from webscout.AIbase import AsyncImageProvider
from webscout.litagent import LitAgent

# Get a fresh user agent! 🔄
agent = LitAgent()

class AsyncPiclumenImager(AsyncImageProvider):
    """Your async homie for generating fire images using Piclumen! ⚡

    This provider generates high-quality AI art with built-in retry logic
    and error handling to make sure you get your images no cap! 💯

    Examples:
        >>> provider = AsyncPiclumenImager()
        >>> 
        >>> # Generate one image with default model
        >>> async def single_image():
        ...     image = await provider.generate("A futuristic city")
        ...     await provider.save(image, "city.jpg")
        >>> 
        >>> # Generate multiple images
        >>> async def multiple_images():
        ...     images = await provider.generate(
        ...         prompt="Underwater alien creatures",
        ...         amount=3
        ...     )
        ...     await provider.save(images, dir="ocean_creatures")
    """

    def __init__(
        self, 
        timeout: int = 120, 
        proxies: Optional[dict] = None
    ):
        """Initialize your AsyncPiclumenImager provider with custom settings

        Examples:
            >>> provider = AsyncPiclumenImager(timeout=180)
            >>> provider = AsyncPiclumenImager(proxies={"http": "http://proxy:8080"})

        Args:
            timeout (int): HTTP request timeout in seconds (default: 120)
            proxies (dict, optional): Proxy configuration for requests
        """
        self.api_endpoint = "https://s9.piclumen.art/comfy/api/generate-image"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://www.piclumen.com",
            "Referer": "https://s9.piclumen.art/",
            "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Gpc": "1",
            "User-Agent": agent.random(),  # Using our fire random agent! 🔥
        }

        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "jpg"

    async def generate(
        self,
        prompt: str,
        amount: int = 1,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> List[bytes]:
        """Generate some fire images from your prompt asynchronously! ⚡

        Examples:
            >>> provider = AsyncPiclumenImager()
            >>> async def example():
            ...     # Basic usage
            ...     images = await provider.generate("Cool art")
            ...     # Generate multiple
            ...     images = await provider.generate(
            ...         prompt="Epic underwater scene",
            ...         amount=3
            ...     )

        Args:
            prompt (str): Your image description
            amount (int): How many images you want (default: 1)
            max_retries (int): Max retry attempts if something fails (default: 3)
            retry_delay (int): Seconds to wait between retries (default: 5)

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

        self.prompt = prompt
        
        # Payload with the prompt
        payload = {
            "prompt": prompt
        }

        async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
            tasks = []
            for i in range(amount):
                tasks.append(self._generate_single(session, payload, i, amount, max_retries, retry_delay))
            
            response = await asyncio.gather(*tasks)

        return response

    async def _generate_single(
        self, 
        session: aiohttp.ClientSession, 
        payload: dict,
        index: int,
        total: int,
        max_retries: int, 
        retry_delay: int
    ) -> bytes:
        """Helper method to generate a single image with retries"""
        for attempt in range(max_retries):
            try:
                async with session.post(self.api_endpoint, json=payload, proxy=self.proxies) as resp:
                    resp.raise_for_status()
                    
                    # Check if response is an image
                    if resp.headers.get('content-type') == 'image/jpeg':
                        content = await resp.read()
                        return content
                    else:
                        error_text = await resp.text()
                        if attempt == max_retries - 1:
                            raise aiohttp.ClientError(f"API returned non-image content: {error_text[:100]}")
            
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    raise
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
            >>> provider = AsyncPiclumenImager()
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

        saved_paths = []
        timestamp = int(time.time())
        
        # Clean up name for filename use
        safe_name = ""
        if name:
            safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
            
        # Use prompt-based name if no name is provided
        if not safe_name and self.prompt:
            # Clean and truncate prompt for filename
            prompt_words = self.prompt.split()[:5]  # First 5 words
            safe_name = "_".join("".join(c if c.isalnum() else "_" for c in word) for word in prompt_words).lower()
        
        async def save_single_image(image_bytes: bytes, index: int) -> str:
            if safe_name:
                filename = f"{filenames_prefix}{safe_name}_{index}.{self.image_extension}"
            else:
                filename = f"{filenames_prefix}piclumen_{timestamp}_{index}.{self.image_extension}"
            
            filepath = os.path.join(save_dir, filename)
            
            # Write file using asyncio
            async with asyncio.Lock():
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
            
            return filepath

        # Handle both List[bytes] and AsyncGenerator
        if isinstance(response, list):
            image_list = response
        else:
            image_list = [chunk async for chunk in response]

        tasks = [save_single_image(img, i) for i, img in enumerate(image_list)]
        saved_paths = await asyncio.gather(*tasks)
        return saved_paths


if __name__ == "__main__":
    # Example usage
    async def main():
        provider = AsyncPiclumenImager()
        try:
            images = await provider.generate(
                prompt="underwater macro photography, alien-like sea creature, translucent body, feathery appendages, glowing orbs",
                amount=2
            )
            paths = await provider.save(images, dir="generated_images")
            print(f"Successfully saved images to: {paths}")
        except Exception as e:
            print(f"Oops, something went wrong: {e}")

    asyncio.run(main())