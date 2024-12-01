import uuid
import json
import os
from typing import Any, Dict, List, Union, AsyncGenerator
import aiohttp
import asyncio
import aiofiles

from webscout.AIbase import AsyncImageProvider
from webscout import exceptions
from webscout.litagent import agent  # Import our fire user agent generator 🔥
from webscout.Litlogger import LitLogger  # For that cyberpunk logging swag ⚡

# Initialize our fire logger 🚀
logger = LitLogger("AsyncTalkaiImager")

class AsyncTalkaiImager(AsyncImageProvider):
    """
    Async TalkAI Image Provider - Your go-to for fire AI art! 🎨
    
    >>> # Generate some fire art asynchronously! 🔥
    >>> async def generate_art():
    ...     imager = AsyncTalkaiImager(logging=True)
    ...     images = await imager.generate("Epic dragon breathing fire", amount=2)
    ...     paths = await imager.save(images)
    ...     print(paths)
    >>> asyncio.run(generate_art())
    ['epic_dragon_0.png', 'epic_dragon_1.png']
    
    >>> # Turn off logging for stealth mode 🥷
    >>> async def stealth_art():
    ...     quiet_imager = AsyncTalkaiImager(logging=False)
    ...     images = await quiet_imager.generate("Cyberpunk city at night")
    ...     paths = await quiet_imager.save(images)
    >>> asyncio.run(stealth_art())
    """

    def __init__(self, timeout: int = 60, proxies: dict = {}, logging: bool = True):
        """Initialize your async TalkAI provider with custom settings! ⚙️

        Args:
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.api_endpoint = "https://talkai.info/chat/send/"
        self.headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://talkai.info',
            'referer': 'https://talkai.info/image/',
            'user-agent': agent.random(),  # Using our fire random agent! 🔥
        }
        self.timeout = timeout
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = logging
        if self.logging:
            logger.info("AsyncTalkaiImager initialized! Ready to create some fire art! 🚀")

    async def generate(
        self, prompt: str, amount: int = 1,
        max_retries: int = 3, retry_delay: int = 5
    ) -> List[str]:
        """Generate some fire images from your prompt! 🎨

        Args:
            prompt (str): Your creative prompt
            amount (int): How many images to generate
            max_retries (int): Max retry attempts if generation fails
            retry_delay (int): Seconds to wait between retries

        Returns:
            List[str]: List of image URLs
        """
        assert bool(prompt), "Prompt cannot be empty."
        assert isinstance(amount, int) and amount > 0, "Amount must be a positive integer."

        self.prompt = prompt
        image_urls = []

        if self.logging:
            logger.info(f"Generating {amount} images... 🎨")

        async with aiohttp.ClientSession(headers=self.headers) as session:
            for _ in range(amount):
                for attempt in range(max_retries):
                    try:
                        async with session.post(
                            self.api_endpoint,
                            json=self._create_payload(prompt),
                            timeout=self.timeout,
                            proxy=self.proxies.get('http') if self.proxies else None
                        ) as response:
                            response.raise_for_status()
                            data = await response.json()

                            if 'data' in data and len(data['data']) > 0 and 'url' in data['data'][0]:
                                image_urls.append(data['data'][0]['url'])
                                if self.logging:
                                    logger.success(f"Generated image {len(image_urls)}/{amount}! 🎨")
                                break
                            else:
                                raise exceptions.InvalidResponseError("No image URL found in API response.")

                    except aiohttp.ClientError as e:
                        if attempt == max_retries - 1:
                            if self.logging:
                                logger.error(f"Error making API request: {e} 😢")
                            raise exceptions.APIConnectionError(f"Error making API request: {e}") from e
                        else:
                            if self.logging:
                                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds... 🔄")
                            await asyncio.sleep(retry_delay)
                    except json.JSONDecodeError as e:
                        if self.logging:
                            logger.error(f"Invalid JSON response: {e} 😢")
                        raise exceptions.InvalidResponseError(f"Invalid JSON response: {e}") from e
                    except Exception as e:
                        if self.logging:
                            logger.error(f"An unexpected error occurred: {e} 😢")
                        raise exceptions.FailedToGenerateResponseError(f"An unexpected error occurred: {e}") from e

        if self.logging:
            logger.success("All images generated successfully! 🎉")
        return image_urls

    def _create_payload(self, prompt: str) -> Dict[str, Any]:
        """Create the API request payload 📦

        Args:
            prompt (str): The image generation prompt

        Returns:
            Dict[str, Any]: API request payload
        """
        return {
            "type": "image",
            "messagesHistory": [
                {
                    "id": str(uuid.uuid4()),
                    "from": "you",
                    "content": prompt
                }
            ],
            "settings": {
                "model": "gpt-4o-mini"  # Or another suitable model if available
            }
        }

    async def save(
        self,
        response: Union[List[str], AsyncGenerator[str, None]],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire images! 💾

        Args:
            response (Union[List[str], AsyncGenerator[str, None]]): Image URLs
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

        async def save_single_image(url: str, index: int) -> str:
            filename = f"{filenames_prefix}{name}_{index}.{self.image_extension}"
            filepath = os.path.join(dir, filename)
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                try:
                    async with session.get(
                        url,
                        timeout=self.timeout,
                        proxy=self.proxies.get('http') if self.proxies else None
                    ) as response:
                        response.raise_for_status()
                        async with aiofiles.open(filepath, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        if self.logging:
                            logger.success(f"Saved image to: {filepath} 💾")
                        return filename
                except aiohttp.ClientError as e:
                    if self.logging:
                        logger.error(f"Error downloading image from {url}: {e} 😢")
                    return None

        if isinstance(response, list):
            url_list = response
        else:
            url_list = [url async for url in response]

        if self.logging:
            logger.info(f"Saving {len(url_list)} images... 💾")

        tasks = [save_single_image(url, i) for i, url in enumerate(url_list)]
        saved_paths = await asyncio.gather(*tasks)

        if self.logging:
            logger.success(f"All images saved successfully! Check {dir} 🎉")
        return saved_paths


if __name__ == "__main__":
    async def main():
        bot = AsyncTalkaiImager()
        try:
            resp = await bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
            paths = await bot.save(resp)
            print(paths)
        except Exception as e:
            if bot.logging:
                logger.error(f"An error occurred: {e} 😢")

    asyncio.run(main())
