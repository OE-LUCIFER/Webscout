import aiohttp
import asyncio
import json
import os
from typing import List, Dict, Optional, Union, AsyncGenerator
import aiofiles

from webscout.AIbase import AsyncImageProvider
from webscout import exceptions
from webscout.litagent import agent  # Import our fire user agent generator 🔥
from webscout.Litlogger import LitLogger  # For that cyberpunk logging swag ⚡

# Initialize our fire logger 🚀
logger = LitLogger("AsyncNinjaImager", "MODERN_EMOJI")

class AsyncNinjaImager(AsyncImageProvider):
    """
    Async image provider for NinjaChat.ai - Your go-to for fire AI art! 🎨
    
    >>> # Generate some fire art asynchronously! 🔥
    >>> async def generate_art():
    ...     imager = AsyncNinjaImager(logging=True)
    ...     images = await imager.generate("Epic dragon breathing fire", amount=2)
    ...     paths = await imager.save(images)
    ...     print(paths)
    >>> asyncio.run(generate_art())
    ['epic_dragon_0.png', 'epic_dragon_1.png']
    
    >>> # Turn off logging for stealth mode 🥷
    >>> async def stealth_art():
    ...     quiet_imager = AsyncNinjaImager(logging=False)
    ...     images = await quiet_imager.generate("Cyberpunk city at night")
    ...     paths = await quiet_imager.save(images)
    >>> asyncio.run(stealth_art())
    """

    AVAILABLE_MODELS = {
        "stable-diffusion": "https://www.ninjachat.ai/api/image-generator",
        "flux-dev": "https://www.ninjachat.ai/api/flux-image-generator",
    }

    def __init__(self, timeout: int = 60, proxies: dict = {}, logging: bool = True):
        """Initialize your async NinjaChatImager with custom settings! ⚙️

        Args:
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://www.ninjachat.ai",
            "Priority": "u=1, i",
            "Referer": "https://www.ninjachat.ai/image-generation",
            "Sec-CH-UA": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": agent.random()  # Using our fire random agent! 🔥
        }
        self.timeout = timeout
        self.proxies = proxies
        self.prompt = "AI-generated image - webscout"
        self.image_extension = "png"
        self.logging = logging
        if self.logging:
            logger.info("AsyncNinjaImager initialized! Ready to create some fire art! 🚀")

    async def generate(
        self, prompt: str, amount: int = 1, model: str = "flux-dev"
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Args:
            prompt (str): Your creative prompt
            amount (int): How many images to generate
            model (str): Which model to use (default: flux-dev)

        Returns:
            List[bytes]: Your generated images as bytes
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int) and amount > 0, "Amount should be a positive integer"

        if model not in self.AVAILABLE_MODELS:
            raise exceptions.ModelNotFoundError(
                f"Model '{model}' not found. Available models: {', '.join(self.AVAILABLE_MODELS)}"
            )

        self.prompt = prompt
        url = self.AVAILABLE_MODELS[model]

        payload = {
            "prompt": prompt,
            "model": model if model == "flux-dev" else "stable-diffusion",
            "negativePrompt": "",
            "cfg": 7,
            "aspectRatio": "1:1",
            "outputFormat": self.image_extension,
            "numOutputs": amount,
            "outputQuality": 90
        }

        if self.logging:
            logger.info(f"Generating {amount} images with {model}... 🎨")

        response = []
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.post(url, json=payload, timeout=self.timeout) as resp:
                    if resp.status != 200:
                        if self.logging:
                            logger.error(f"Request failed with status {resp.status} 😢")
                        raise exceptions.FailedToGenerateResponseError(
                            f"Request failed with status code: {resp.status}, {await resp.text()}"
                        )

                    data = await resp.json()

                    if 'output' not in data:
                        if self.logging:
                            logger.error("Invalid API response format 😢")
                        raise exceptions.InvalidResponseError("Invalid API response format: 'output' key missing.")

                    for img_url in data['output']:
                        async with session.get(img_url) as img_resp:
                            img_resp.raise_for_status()
                            response.append(await img_resp.read())
                            if self.logging:
                                logger.success(f"Generated image {len(response)}/{amount}! 🎨")

            except aiohttp.ClientError as e:
                if self.logging:
                    logger.error(f"Connection error: {e} 😢")
                raise exceptions.APIConnectionError(f"An error occurred during the request: {e}")
            except json.JSONDecodeError as e:
                if self.logging:
                    logger.error(f"Failed to parse response: {e} 😢")
                raise exceptions.InvalidResponseError(f"Failed to parse JSON response: {e}")

        if self.logging:
            logger.success("All images generated successfully! 🎉")
        return response

    async def save(
        self,
        response: Union[List[bytes], AsyncGenerator[bytes, None]],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire images! 💾

        Args:
            response (Union[List[bytes], AsyncGenerator[bytes, None]]): Image data
            name (str, optional): Base name for saved files
            dir (str, optional): Where to save the images
            filenames_prefix (str, optional): Prefix for filenames

        Returns:
            List[str]: List of saved filenames
        """
        if not os.path.exists(dir):
            os.makedirs(dir)
            if self.logging:
                logger.info(f"Created directory: {dir} 📁")

        name = self.prompt if name is None else name
        saved_paths = []

        async def save_single_image(image_bytes: bytes, index: int) -> str:
            filename = f"{filenames_prefix}{name}_{index}.{self.image_extension}"
            filepath = os.path.join(dir, filename)
            
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(image_bytes)
            
            if self.logging:
                logger.success(f"Saved image to: {filepath} 💾")
            return filename

        if isinstance(response, list):
            image_list = response
        else:
            image_list = [chunk async for chunk in response]

        if self.logging:
            logger.info(f"Saving {len(image_list)} images... 💾")

        tasks = [save_single_image(img, i) for i, img in enumerate(image_list)]
        saved_paths = await asyncio.gather(*tasks)

        if self.logging:
            logger.success(f"All images saved successfully! Check {dir} 🎉")
        return saved_paths


if __name__ == "__main__":
    async def main():
        bot = AsyncNinjaImager()
        try:
            resp = await bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
            paths = await bot.save(resp)
            print(paths)
        except Exception as e:
            print(f"An error occurred: {e}")

    asyncio.run(main())
