"""
AsyncArtbitImager - Your go-to async provider for generating fire images with Artbit! ⚡

Examples:
    >>> from webscout import AsyncArtbitImager
    >>> import asyncio
    >>> 
    >>> async def example():
    ...     # Initialize with logging
    ...     provider = AsyncArtbitImager(logging=True)
    ...     
    ...     # Generate a single image
    ...     images = await provider.generate("Cool art")
    ...     paths = await provider.save(images)
    ...     
    ...     # Generate multiple images with parameters
    ...     images = await provider.generate(
    ...         prompt="Epic dragon in cyberpunk city",
    ...         amount=3,
    ...         caption_model="sdxl",
    ...         selected_ratio="1024",
    ...         negative_prompt="blurry, bad quality"
    ...     )
    ...     paths = await provider.save(images, name="dragon", dir="outputs")
    >>> 
    >>> # Run the example
    >>> asyncio.run(example())
"""

import aiohttp
import aiofiles
import asyncio
import os
from typing import List
from webscout.AIbase import AsyncImageProvider
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent import LitAgent

# Initialize our fire logger and agent 🔥
logger = LitLogger(
    "AsyncArtbit",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK
)
agent = LitAgent()

class AsyncArtbitImager(AsyncImageProvider):
    """Your go-to async provider for generating fire images with Artbit! ⚡"""

    def __init__(self, timeout: int = 60, proxies: dict = {}, logging: bool = True):
        """Initialize your async Artbit provider with custom settings! ⚙️

        Args:
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.url = "https://artbit.ai/api/generateImage"
        self.headers = {
            "User-Agent": agent.random(),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.timeout = timeout
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = logging
        if self.logging:
            logger.info("AsyncArtbit provider initialized! 🚀")

    async def generate(
        self, 
        prompt: str, 
        amount: int = 1,
        caption_model: str = "sdxl",
        selected_ratio: str = "1024",
        negative_prompt: str = ""
    ) -> List[str]:
        """Generate some fire images asynchronously! ⚡

        Args:
            prompt (str): Your lit image description
            amount (int): How many images to generate (default: 1)
            caption_model (str): Which model to use (default: "sdxl")
            selected_ratio (str): Image size ratio (default: "1024")
            negative_prompt (str): What you don't want in the image (default: "")

        Returns:
            List[str]: Your generated image URLs
        """
        assert bool(prompt), "Yo fam, prompt can't be empty! 🚫"
        assert isinstance(amount, int), f"Amount gotta be an integer, not {type(amount)} 🤔"
        assert amount > 0, "Amount gotta be greater than 0! 📈"

        self.prompt = prompt
        response: List[str] = []

        if self.logging:
            logger.info(f"Generating {amount} images with {caption_model}... 🎨")

        payload = {
            "captionInput": prompt,
            "captionModel": caption_model,
            "selectedRatio": selected_ratio,
            "selectedSamples": str(amount),
            "negative_prompt": negative_prompt
        }

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(self.url, json=payload, timeout=self.timeout) as resp:
                    resp.raise_for_status()
                    response_data = await resp.json()
                    imgs = response_data.get("imgs", [])
                    
                    if imgs:
                        response.extend(imgs)
                        if self.logging:
                            logger.success("Images generated successfully! 🎉")
                    else:
                        if self.logging:
                            logger.warning("No images found in the response 😢")

        except aiohttp.ClientError as e:
            if self.logging:
                logger.error(f"Failed to generate images: {e} 😢")
            raise

        return response

    async def save(
        self,
        response: List[str],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire images asynchronously! 💾

        Args:
            response (List[str]): Your image URLs to save
            name (str, optional): Custom name (default: uses prompt)
            dir (str, optional): Where to save (default: current directory)
            filenames_prefix (str, optional): Add prefix to filenames

        Returns:
            List[str]: Where your images were saved
        """
        assert isinstance(response, list), f"Response gotta be a list, not {type(response)} 🤔"
        name = self.prompt if name is None else name

        filenames = []
        count = 0

        if self.logging:
            logger.info(f"Saving {len(response)} images... 💾")

        async with aiohttp.ClientSession(headers=self.headers) as session:
            for img_url in response:
                def complete_path():
                    count_value = "" if count == 0 else f"_{count}"
                    return os.path.join(dir, name + count_value + "." + self.image_extension)

                while os.path.isfile(complete_path()):
                    count += 1

                absolute_path_to_file = complete_path()
                filenames.append(filenames_prefix + os.path.split(absolute_path_to_file)[1])

                try:
                    async with session.get(img_url, timeout=self.timeout) as resp:
                        resp.raise_for_status()
                        async with aiofiles.open(absolute_path_to_file, "wb") as fh:
                            await fh.write(await resp.read())

                except aiohttp.ClientError as e:
                    if self.logging:
                        logger.error(f"Failed to save image from {img_url}: {e} 😢")
                    raise

        if self.logging:
            logger.success(f"Images saved successfully! Check {dir} 🎉")
        return filenames
