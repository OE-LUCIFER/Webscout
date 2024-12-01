import aiohttp
import asyncio
import os
import time
from typing import List, Optional, Union, AsyncGenerator
from string import punctuation
from random import choice
from aiohttp import ClientError
from pathlib import Path

from webscout.AIbase import AsyncImageProvider
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent import LitAgent

# Initialize our fire logger and agent 🔥
logger = LitLogger(
    "AsyncAiForce",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK
)
agent = LitAgent()

class AsyncAiForceimager(AsyncImageProvider):
    """Your go-to async provider for generating fire images with AiForce! ⚡

    Examples:
        >>> # Basic usage
        >>> provider = AsyncAiForceimager()
        >>> async def example():
        ...     images = await provider.generate("Cool art")
        ...     paths = await provider.save(images)
        >>>
        >>> # Advanced usage
        >>> provider = AsyncAiForceimager(timeout=120)
        >>> async def example():
        ...     images = await provider.generate(
        ...         prompt="Epic dragon",
        ...         amount=3,
        ...         model="Flux-1.1-Pro",
        ...         width=1024,
        ...         height=1024
        ...     )
        ...     paths = await provider.save(images, name="dragon", dir="my_art")
    """

    AVAILABLE_MODELS = [
        "stable-diffusion-xl-lightning",
        "stable-diffusion-xl-base",
        "Flux-1.1-Pro",
        "ideogram",
        "flux",
        "flux-realism",
        "flux-anime",
        "flux-3d",
        "flux-disney",
        "flux-pixel",
        "flux-4o",
        "any-dark"
    ]

    def __init__(self, timeout: int = 60, proxies: dict = {}, logging: bool = True):
        """Initialize your async AiForce provider with custom settings! ⚙️

        Args:
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.api_endpoint = "https://api.airforce/imagine2"
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": agent.random()
        }
        self.timeout = timeout
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = logging
        if self.logging:
            logger.info("AsyncAiForce provider initialized! 🚀")

    async def generate(
        self, 
        prompt: str, 
        amount: int = 1, 
        additives: bool = True,
        model: str = "Flux-1.1-Pro", 
        width: int = 768, 
        height: int = 768, 
        seed: Optional[int] = None,
        max_retries: int = 3, 
        retry_delay: int = 5
    ) -> List[bytes]:
        """Generate some fire images from your prompt asynchronously! ⚡

        Examples:
            >>> provider = AsyncAiForceimager()
            >>> async def example():
            ...     # Basic usage
            ...     images = await provider.generate("Cool art")
            ...     # Advanced usage
            ...     images = await provider.generate(
            ...         prompt="Epic dragon",
            ...         amount=3,
            ...         model="Flux-1.1-Pro"
            ...     )

        Args:
            prompt (str): Your image description
            amount (int): How many images you want (default: 1)
            additives (bool): Make each prompt unique (default: True)
            model (str): Model to use - check AVAILABLE_MODELS (default: "Flux-1.1-Pro")
            width (int): Image width (default: 768)
            height (int): Image height (default: 768)
            seed (int, optional): Seed for reproducible results
            max_retries (int): Max retry attempts if something fails (default: 3)
            retry_delay (int): Seconds to wait between retries (default: 5)

        Returns:
            List[bytes]: Your generated images

        Raises:
            ValueError: If the inputs ain't valid
            ClientError: If the API calls fail after retries
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"
        assert model in self.AVAILABLE_MODELS, f"Model should be one of {self.AVAILABLE_MODELS}"

        ads = lambda: (
            ""
            if not additives
            else choice(punctuation)
            + choice(punctuation)
            + choice(punctuation)
            + choice(punctuation)
            + choice(punctuation)
        )

        self.prompt = prompt
        response = []
        
        if self.logging:
            logger.info(f"Generating {amount} images with {model}... 🎨")
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for i in range(amount):
                url = f"{self.api_endpoint}?model={model}&prompt={prompt}&size={width}:{height}"
                if seed:
                    url += f"&seed={seed}"
                
                for attempt in range(max_retries):
                    try:
                        async with session.get(url, timeout=self.timeout, proxy=self.proxies.get('http')) as resp:
                            resp.raise_for_status()
                            response.append(await resp.read())
                            if self.logging:
                                logger.success(f"Generated image {i + 1}/{amount}! 🎨")
                            break
                    except ClientError as e:
                        if attempt == max_retries - 1:
                            if self.logging:
                                logger.error(f"Failed to generate image after {max_retries} attempts: {e} 😢")
                            raise
                        else:
                            if self.logging:
                                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds... 🔄")
                            await asyncio.sleep(retry_delay)

        if self.logging:
            logger.success("Images generated successfully! 🎉")
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
            >>> provider = AsyncAiForceimager()
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
            if self.logging:
                logger.info(f"Created directory: {save_dir} 📁")

        name = self.prompt if name is None else name
        saved_paths = []
        timestamp = int(time.time())
        
        if self.logging:
            logger.info(f"Saving {len(response)} images... 💾")
        
        async def save_single_image(image_bytes: bytes, index: int) -> str:
            filename = f"{filenames_prefix}{name}_{index}.{self.image_extension}"
            filepath = os.path.join(save_dir, filename)
            
            # Write file using asyncio
            async with asyncio.Lock():
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
            
            if self.logging:
                logger.success(f"Saved image to: {filepath} 💾")
            return filepath

        # Handle both List[bytes] and AsyncGenerator
        if isinstance(response, list):
            image_list = response
        else:
            image_list = [chunk async for chunk in response]

        tasks = [save_single_image(img, i) for i, img in enumerate(image_list)]
        saved_paths = await asyncio.gather(*tasks)
        if self.logging:
            logger.success(f"Images saved successfully! Check {dir} 🎉")
        return saved_paths

if __name__ == "__main__":
    async def main():
        bot = AsyncAiForceimager()
        try:
            resp = await bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
            paths = await bot.save(resp)
            print(paths)
        except Exception as e:
            logger.error(f"An error occurred: {e} 😢")

    asyncio.run(main())
