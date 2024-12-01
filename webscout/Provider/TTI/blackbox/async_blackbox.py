import aiohttp
import asyncio
import json
import uuid
import os
from typing import List, Union, AsyncGenerator
import aiofiles

from webscout.AIbase import AsyncImageProvider
from webscout.litagent import LitAgent  # Import our fire user agent generator 🔥
from webscout.Litlogger import LitLogger  # For that cyberpunk logging swag ⚡

# Initialize our fire logger 🚀
logger = LitLogger("AsyncBlackboxAIImager")

class AsyncBlackboxAIImager(AsyncImageProvider):
    """
    Async BlackboxAI Image Provider - Your go-to for fire AI art! 🎨
    
    >>> # Generate some fire art asynchronously! 🔥
    >>> async def generate_art():
    ...     imager = AsyncBlackboxAIImager(logging=True)
    ...     images = await imager.generate("Epic dragon breathing fire", amount=2)
    ...     paths = await imager.save(images)
    ...     print(paths)
    >>> asyncio.run(generate_art())
    ['epic_dragon_0.jpg', 'epic_dragon_1.jpg']
    
    >>> # Turn off logging for stealth mode 🥷
    >>> async def stealth_art():
    ...     quiet_imager = AsyncBlackboxAIImager(logging=False)
    ...     images = await quiet_imager.generate("Cyberpunk city at night")
    ...     paths = await quiet_imager.save(images)
    >>> asyncio.run(stealth_art())
    """

    def __init__(self, timeout: int = 60, proxies: dict = {}, logging: bool = True):
        """Initialize your async BlackboxAI provider with custom settings! ⚙️

        Args:
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.url = "https://www.blackbox.ai/api/chat"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": LitAgent().random(),  # Using our fire random agent! 🔥
            "DNT": "1",
            "Origin": "https://www.blackbox.ai",
            "Referer": "https://www.blackbox.ai/agent/ImageGenerationLV45LJp"
        }
        self.timeout = timeout
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "jpg"
        self.logging = logging
        if self.logging:
            logger.info("AsyncBlackboxAIImager initialized! Ready to create some fire art! 🚀")

    async def generate(
        self, prompt: str, amount: int = 1,
        max_retries: int = 3, retry_delay: int = 5
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Args:
            prompt (str): Your creative prompt
            amount (int): How many images to generate
            max_retries (int): Max retry attempts if generation fails
            retry_delay (int): Seconds to wait between retries

        Returns:
            List[bytes]: Your generated images as bytes
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"

        self.prompt = prompt
        response = []

        if self.logging:
            logger.info(f"Generating {amount} images... 🎨")

        async with aiohttp.ClientSession(headers=self.headers) as session:
            for _ in range(amount):
                message_id = str(uuid.uuid4())
                payload = {
                    "messages": [
                        {
                            "id": message_id,
                            "content": prompt,
                            "role": "user"
                        }
                    ],
                    "id": message_id,
                    "previewToken": None,
                    "userId": None,
                    "codeModelMode": True,
                    "agentMode": {
                        "mode": True,
                        "id": "ImageGenerationLV45LJp",
                        "name": "Image Generation"
                    },
                    "trendingAgentMode": {},
                    "isMicMode": False,
                    "maxTokens": 1024,
                    "isChromeExt": False,
                    "githubToken": None,
                    "clickedAnswer2": False,
                    "clickedAnswer3": False,
                    "clickedForceWebSearch": False,
                    "visitFromDelta": False,
                    "mobileClient": False
                }

                for attempt in range(max_retries):
                    try:
                        async with session.post(self.url, json=payload, timeout=self.timeout) as resp:
                            resp.raise_for_status()
                            response_data = await resp.text()
                            image_url = response_data.split("(")[1].split(")")[0]
                            
                            async with session.get(image_url) as image_resp:
                                image_resp.raise_for_status()
                                response.append(await image_resp.read())
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
        bot = AsyncBlackboxAIImager()
        try:
            resp = await bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
            paths = await bot.save(resp)
            print(paths)
        except Exception as e:
            if bot.logging:
                logger.error(f"An error occurred: {e} 😢")

    asyncio.run(main())
