import aiohttp
import asyncio
import os
import uuid
import time
from typing import List, Optional, Union, AsyncGenerator
from pathlib import Path

from webscout.AIbase import AsyncImageProvider
from webscout.litagent import LitAgent

agent = LitAgent()

class AsyncMagicStudioImager(AsyncImageProvider):
    """Your go-to async provider for generating fire images with MagicStudio! ⚡"""
    
    def __init__(self, timeout: int = 60, proxies: dict = None):
        """Initialize your async MagicStudio provider with custom settings! ⚙️"""
        self.api_endpoint = "https://ai-api.magicstudio.com/api/ai-art-generator"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": agent.random(),
            "Origin": "https://magicstudio.com",
            "Referer": "https://magicstudio.com/ai-art-generator/",
            "DNT": "1",
            "Sec-GPC": "1"
        }
        self.timeout = timeout
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
        """Generate some fire images from your prompt asynchronously! ⚡"""
        if not prompt:
            raise ValueError("Yo fam, prompt can't be empty! 🚫")
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Amount needs to be a positive number! 📈")

        self.prompt = prompt
        response = []

        async with aiohttp.ClientSession(headers=self.headers) as session:
            for _ in range(amount):
                form_data = {
                    "prompt": prompt,
                    "output_format": "bytes",
                    "user_profile_id": "null",
                    "anonymous_user_id": str(uuid.uuid4()),
                    "request_timestamp": time.time(),
                    "user_is_subscribed": "false",
                    "client_id": uuid.uuid4().hex,
                }

                for attempt in range(max_retries):
                    try:
                        async with session.post(
                            self.api_endpoint,
                            data=form_data,
                            timeout=self.timeout,
                            proxy=self.proxies.get('http') if self.proxies else None
                        ) as resp:
                            resp.raise_for_status()
                            response.append(await resp.read())
                            break
                    except aiohttp.ClientError as e:
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(retry_delay)

        return response

    async def save(
        self,
        response: Union[List[bytes], AsyncGenerator[bytes, None]],
        name: Optional[str] = None,
        dir: Optional[Union[str, Path]] = None,
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire generated images asynchronously! 💾"""
        save_dir = dir if dir else os.getcwd()
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        name = self.prompt if name is None else name
        saved_paths = []

        async def save_single_image(image_bytes: bytes, index: int) -> str:
            filename = f"{filenames_prefix}{name}_{index}.{self.image_extension}"
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            return os.path.basename(filepath)

        if isinstance(response, list):
            image_list = response
        else:
            image_list = [chunk async for chunk in response]

        tasks = [save_single_image(img, i) for i, img in enumerate(image_list)]
        saved_paths = await asyncio.gather(*tasks)
        
        return saved_paths
