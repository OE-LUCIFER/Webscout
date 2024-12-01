import aiohttp
import asyncio
import os
import base64
from typing import List, Union, AsyncGenerator
from string import punctuation
from random import choice
from random import randint
import aiofiles

from webscout.AIbase import AsyncImageProvider
from webscout.litagent import LitAgent  # Import our fire user agent generator 🔥
from webscout.Litlogger import LitLogger  # For that cyberpunk logging swag ⚡

# Initialize our fire logger 🚀
logger = LitLogger("AsyncDeepInfraImager")

class AsyncDeepInfraImager(AsyncImageProvider):
    """
    Async DeepInfra Image Provider - Your go-to for fire AI art! 🎨
    
    >>> # Generate some fire art asynchronously! 🔥
    >>> async def generate_art():
    ...     imager = AsyncDeepInfraImager(logging=True)
    ...     images = await imager.generate("Epic dragon breathing fire", amount=2)
    ...     paths = await imager.save(images)
    ...     print(paths)
    >>> asyncio.run(generate_art())
    ['epic_dragon_0.png', 'epic_dragon_1.png']
    
    >>> # Turn off logging for stealth mode 🥷
    >>> async def stealth_art():
    ...     quiet_imager = AsyncDeepInfraImager(logging=False)
    ...     images = await quiet_imager.generate("Cyberpunk city at night")
    ...     paths = await quiet_imager.save(images)
    >>> asyncio.run(stealth_art())
    """

    def __init__(
        self,
        model: str = "black-forest-labs/FLUX-1-schnell",
        timeout: int = 60,
        proxies: dict = {},
        logging: bool = True
    ):
        """Initialize your async DeepInfra provider with custom settings! ⚙️

        Args:
            model (str): Which model to use (default: black-forest-labs/FLUX-1-schnell)
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.image_gen_endpoint: str = f"https://api.deepinfra.com/v1/inference/{model}"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": LitAgent().random(),  # Using our fire random agent! 🔥
            "DNT": "1",
            "Origin": "https://deepinfra.com",
            "Referer": "https://deepinfra.com/",
            "Sec-CH-UA": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        self.timeout = timeout
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = logging
        if self.logging:
            logger.info("AsyncDeepInfraImager initialized! Ready to create some fire art! 🚀")

    async def generate(
        self, prompt: str, amount: int = 1, additives: bool = True,
        num_inference_steps: int = 25, guidance_scale: float = 7.5,
        width: int = 1024, height: int = 1024, seed: int = None,
        max_retries: int = 3, retry_delay: int = 5
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Args:
            prompt (str): Your creative prompt
            amount (int): How many images to generate
            additives (bool): Add random characters to make prompts unique
            num_inference_steps (int): Number of inference steps
            guidance_scale (float): Guidance scale for generation
            width (int): Image width
            height (int): Image height
            seed (int, optional): Random seed for reproducibility
            max_retries (int): Max retry attempts if generation fails
            retry_delay (int): Seconds to wait between retries

        Returns:
            List[bytes]: Your generated images as bytes
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"

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
            logger.info(f"Generating {amount} images... 🎨")

        async with aiohttp.ClientSession(headers=self.headers) as session:
            for _ in range(amount):
                payload = {
                    "prompt": prompt + ads(),
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "width": width,
                    "height": height,
                    "seed": seed if seed is not None else randint(1, 10000),
                }

                for attempt in range(max_retries):
                    try:
                        async with session.post(
                            self.image_gen_endpoint,
                            json=payload,
                            timeout=self.timeout,
                            proxy=self.proxies.get('http') if self.proxies else None
                        ) as resp:
                            resp.raise_for_status()
                            data = await resp.json()
                            # Extract base64 encoded image data and decode it
                            image_data = data['images'][0].split(",")[1]
                            image_bytes = base64.b64decode(image_data)
                            response.append(image_bytes)
                            if self.logging:
                                logger.success(f"Generated image {len(response)}/{amount}! 🎨")
                            break
                    except aiohttp.ClientError as e:
                        if attempt == max_retries - 1:
                            if self.logging:
                                logger.error(f"Failed to generate image after {max_retries} attempts: {e} 😢")
                            raise
                        else:
                            if self.logging:
                                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds... 🔄")
                            await asyncio.sleep(retry_delay)

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
        bot = AsyncDeepInfraImager()
        try:
            resp = await bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
            paths = await bot.save(resp)
            print(paths)
        except Exception as e:
            if bot.logging:
                logger.error(f"An error occurred: {e} 😢")

    asyncio.run(main())
