"""AsyncFastFluxImager - Generate stunning AI art with FastFlux (async version)! ⚡

Examples:
    >>> from webscout import AsyncFastFluxImager
    >>> import asyncio
    >>> 
    >>> async def main():
    ...     provider = AsyncFastFluxImager()
    ...     # Generate a single image
    ...     images = await provider.generate("A cool cyberpunk city at night")
    ...     paths = await provider.save(images, dir="my_images")
    ...     print(f"Saved images to: {paths}")
    ... 
    >>> asyncio.run(main())
"""

import aiohttp
import asyncio
import base64
import os
import time
from typing import List, Optional, Union, AsyncGenerator
from pathlib import Path
import aiofiles

from webscout.AIbase import AsyncImageProvider
from webscout.litagent import LitAgent

class AsyncFastFluxImager(AsyncImageProvider):
    """Your go-to async provider for generating fire images with FastFlux! ⚡

    Examples:
        >>> provider = AsyncFastFluxImager()
        >>> 
        >>> # Generate one image with default model
        >>> async def single_image():
        ...     image = await provider.generate("A futuristic city")
        ...     await provider.save(image, "city.png")
        >>> 
        >>> # Generate multiple with specific model
        >>> async def multiple_images():
        ...     images = await provider.generate(
        ...         prompt="Space station",
        ...         amount=3,
        ...         model="flux_1_dev",
        ...         size="16_9"
        ...     )
        ...     await provider.save(images, dir="space_pics")
    """

    AVAILABLE_MODELS = [
        "flux_1_schnell",  # Fast generation model (default)
        "flux_1_dev",      # Developer model
        "sana_1_6b"        # SANA 1.6B model
    ]
    
    AVAILABLE_SIZES = [
        "1_1",
        "16_9",
        "4_3",
    ]

    def __init__(self, timeout: int = 60, proxies: dict = None):
        """Initialize your async FastFluxImager provider with custom settings ⚙️

        Examples:
            >>> provider = AsyncFastFluxImager(timeout=120)
            >>> provider = AsyncFastFluxImager(proxies={"http": "http://proxy:8080"})

        Args:
            timeout (int): HTTP request timeout in seconds (default: 60)
            proxies (dict, optional): Proxy configuration for requests
            logging (bool): Enable/disable logging (default: True)
        """
        self.api_endpoint = "https://api.fastflux.co/v1/images/generate"
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://fastflux.co",
            "referer": "https://fastflux.co/",
            "user-agent": LitAgent().random()
        }
        self.timeout = timeout
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = True


    async def generate(
        self,
        prompt: str,
        amount: int = 1,
        model: str = "flux_1_schnell",
        size: str = "1_1",
        is_public: bool = False,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> List[bytes]:
        """Generate some fire images from your prompt asynchronously! ⚡

        Examples:
            >>> provider = AsyncFastFluxImager()
            >>> async def example():
            ...     # Basic usage
            ...     images = await provider.generate("Cool art")
            ...     # Advanced usage
            ...     images = await provider.generate(
            ...         prompt="Epic dragon",
            ...         amount=2,
            ...         model="flux_1_dev",
            ...         size="16_9"
            ...     )

        Args:
            prompt (str): Your image description
            amount (int): How many images you want (default: 1)
            model (str): Model to use - check AVAILABLE_MODELS (default: "flux_1_schnell")
            size (str): Image size ratio (default: "1_1")
            is_public (bool): Whether to make the image public (default: False)
            max_retries (int): Max retry attempts if something fails (default: 3)
            retry_delay (int): Seconds to wait between retries (default: 5)

        Returns:
            List[bytes]: Your generated images

        Raises:
            ValueError: If the inputs ain't valid
            aiohttp.ClientError: If the API calls fail after retries
        """
        if not prompt:
            raise ValueError("Yo fam, the prompt can't be empty! 🤔")
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Amount needs to be a positive number! 📈")
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model must be one of {self.AVAILABLE_MODELS}! 🎯")
        if size not in self.AVAILABLE_SIZES:
            raise ValueError(f"Size must be one of {self.AVAILABLE_SIZES}! 📏")

        self.prompt = prompt
        response = []

        # Prepare payload
        payload = {
            "prompt": prompt,
            "model": model,
            "size": size,
            "isPublic": is_public
        }


        async with aiohttp.ClientSession(headers=self.headers) as session:
            for i in range(amount):
                for attempt in range(max_retries):
                    try:                        
                        async with session.post(
                            self.api_endpoint,
                            json=payload,
                            timeout=self.timeout,
                            proxy=self.proxies.get('http') if self.proxies else None
                        ) as resp:
                            resp.raise_for_status()
                            result = await resp.json()
                            
                            if result and 'result' in result:
                                # Get base64 data and remove header
                                image_data = result['result']
                                base64_data = image_data.split(',')[1]
                                
                                # Decode base64 data
                                image_bytes = base64.b64decode(base64_data)
                                response.append(image_bytes)
                                break
                            else:
                                raise aiohttp.ClientError("Invalid response format")
                                
                    except aiohttp.ClientError as e:
                        if attempt == max_retries - 1:
                            raise aiohttp.ClientError(f"Failed to generate image after {max_retries} attempts: {e}")
                        await asyncio.sleep(retry_delay)

        return response

    async def save(
        self,
        response: Union[AsyncGenerator[bytes, None], List[bytes]],
        name: Optional[str] = None,
        dir: Optional[Union[str, Path]] = None,
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire generated images asynchronously! 💾

        Examples:
            >>> provider = AsyncFastFluxImager()
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


        name = self.prompt if name is None else name
        
        # Clean up name for filename use
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
        safe_name = safe_name[:50]  # Truncate if too long
        
        # Handle both List[bytes] and AsyncGenerator
        if isinstance(response, list):
            image_list = response
        else:
            image_list = [chunk async for chunk in response]


        async def save_single_image(image_bytes: bytes, index: int) -> str:
            filename = f"{filenames_prefix}{safe_name}_{index}.{self.image_extension}"
            filepath = os.path.join(save_dir, filename)
            
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(image_bytes)

            return filename

        tasks = [save_single_image(img, i) for i, img in enumerate(image_list)]
        saved_paths = await asyncio.gather(*tasks)


        return saved_paths


if __name__ == "__main__":
    # Example usage
    async def main():
        provider = AsyncFastFluxImager()
        try:
            images = await provider.generate("A cyberpunk city at night with neon lights", amount=1)
            paths = await provider.save(images, dir="generated_images")
            print(f"Successfully saved images to: {paths}")
        except Exception as e:
            print(f"Oops, something went wrong: {e}")

    asyncio.run(main())
