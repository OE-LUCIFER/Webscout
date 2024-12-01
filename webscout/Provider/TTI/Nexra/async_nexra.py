import aiohttp
import asyncio
import json
import os
import time
from typing import List, Optional, Union, AsyncGenerator
from pathlib import Path
from aiohttp import ClientError

from webscout.AIbase import AsyncImageProvider
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent import LitAgent

# Initialize our fire logger and agent 🔥
logger = LitLogger(
    "AsyncNexra",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK
)
agent = LitAgent()

class AsyncNexraImager(AsyncImageProvider):
    """Your go-to async provider for generating fire images with Nexra! ⚡

    Examples:
        >>> # Basic usage
        >>> provider = AsyncNexraImager()
        >>> async def example():
        ...     images = await provider.generate("Cool art")
        ...     paths = await provider.save(images)
        >>>
        >>> # Advanced usage
        >>> provider = AsyncNexraImager(timeout=120)
        >>> async def example():
        ...     images = await provider.generate(
        ...         prompt="Epic dragon",
        ...         model="midjourney",
        ...         additional_params={
        ...             "data": {
        ...                 "steps": 30,
        ...                 "cfg_scale": 8
        ...             }
        ...         }
        ...     )
        ...     paths = await provider.save(images, name="dragon", dir="my_art")
    """

    AVAILABLE_MODELS = {
        "standard": [
            "emi",
            "stablediffusion-1.5",
            "stablediffusion-2.1",
            "sdxl-lora",
            "dalle",
            "dalle2",
            "dalle-mini",
            "flux",
            "midjourney"
        ],
        "prodia": [
            "dreamshaperXL10_alpha2.safetensors [c8afe2ef]",
            "dynavisionXL_0411.safetensors [c39cc051]",
            "juggernautXL_v45.safetensors [e75f5471]",
            "realismEngineSDXL_v10.safetensors [af771c3f]",
            "sd_xl_base_1.0.safetensors [be9edd61]",
            "animagineXLV3_v30.safetensors [75f2f05b]",
            "sd_xl_base_1.0_inpainting_0.1.safetensors [5679a81a]",
            "turbovisionXL_v431.safetensors [78890989]",
            "devlishphotorealism_sdxl15.safetensors [77cba69f]",
            "realvisxlV40.safetensors [f7fdcb51]"
        ]
    }

    def __init__(self, timeout: int = 60, proxies: dict = {}, logging: bool = True):
        """Initialize your async Nexra provider with custom settings! ⚙️

        Args:
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.url = "https://nexra.aryahcr.cc/api/image/complements"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": agent.random()
        }
        self.timeout = timeout
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = logging
        if self.logging:
            logger.info("AsyncNexra provider initialized! 🚀")

    async def generate(
        self,
        prompt: str,
        model: str = "midjourney",
        amount: int = 1,
        max_retries: int = 3,
        retry_delay: int = 5,
        additional_params: Optional[dict] = None
    ) -> List[bytes]:
        """Generate some fire images from your prompt asynchronously! ⚡

        Examples:
            >>> provider = AsyncNexraImager()
            >>> async def example():
            ...     # Basic usage
            ...     images = await provider.generate("Cool art")
            ...     # Advanced usage
            ...     images = await provider.generate(
            ...         prompt="Epic dragon",
            ...         model="midjourney",
            ...         amount=3,
            ...         additional_params={"data": {"steps": 30}}
            ...     )

        Args:
            prompt (str): Your image description
            model (str): Model to use (default: "midjourney")
            amount (int): How many images you want (default: 1)
            max_retries (int): Max retry attempts if something fails (default: 3)
            retry_delay (int): Seconds to wait between retries (default: 5)
            additional_params (dict, optional): Extra params for the API

        Returns:
            List[bytes]: Your generated images

        Raises:
            ValueError: If the inputs ain't valid
            ClientError: If the API calls fail after retries
            json.JSONDecodeError: If the API response is invalid
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int) and amount > 0, "Amount should be a positive integer"
        
        all_models = self.AVAILABLE_MODELS["standard"] + self.AVAILABLE_MODELS["prodia"]
        assert model in all_models, f"Model should be one of {all_models}"

        self.prompt = prompt
        response = []

        payload = {
            "prompt": prompt,
            "model": "prodia" if model in self.AVAILABLE_MODELS["prodia"] else model,
        }

        if model in self.AVAILABLE_MODELS["prodia"]:
            payload["data"] = {
                "model": model,
                "steps": 25,
                "cfg_scale": 7,
                "sampler": "DPM++ 2M Karras",
                "negative_prompt": ""
            }
        if additional_params:
            payload.update(additional_params)

        async with aiohttp.ClientSession(headers=self.headers) as session:
            for attempt in range(max_retries):
                try:
                    if self.logging:
                        logger.info(f"Generating {amount} images with {model}... 🎨")
                    async with session.post(
                        self.url,
                        json=payload,
                        timeout=self.timeout,
                        proxy=self.proxies.get('http')
                    ) as resp:
                        resp.raise_for_status()
                        text = await resp.text()

                        # Remove leading underscores and then parse JSON
                        response_data = json.loads(text.lstrip("_"))

                        if response_data.get("status") and "images" in response_data:
                            for image_url in response_data["images"]:
                                async with session.get(image_url) as img_resp:
                                    img_resp.raise_for_status()
                                    response.append(await img_resp.read())
                                    if self.logging:
                                        logger.success(f"Generated image {len(response)}/{amount}! 🎨")
                            break
                        else:
                            raise Exception("Failed to generate image: " + str(response_data))
                except json.JSONDecodeError as json_err:
                    if self.logging:
                        logger.error(f"JSON Decode Error: {json_err} 😢")
                    logger.debug(f"Raw response: {text}")
                    if attempt == max_retries - 1:
                        raise
                except ClientError as e:
                    if self.logging:
                        logger.error(f"Failed to generate images: {e} 😢")
                    if attempt == max_retries - 1:
                        raise
                if self.logging:
                    logger.warning(f"Retrying in {retry_delay} seconds... 🔄")
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
            >>> provider = AsyncNexraImager()
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

        if self.logging:
            logger.info(f"Saving {len(image_list)} images... 💾")
        tasks = [save_single_image(img, i) for i, img in enumerate(image_list)]
        saved_paths = await asyncio.gather(*tasks)
        if self.logging:
            logger.success(f"Images saved successfully! Check {dir} 🎉")
        return saved_paths

if __name__ == "__main__":
    async def main():
        bot = AsyncNexraImager()
        try:
            resp = await bot.generate("A shiny red sports car speeding down a scenic mountain road", "midjourney")
            paths = await bot.save(resp)
            print(paths)
        except Exception as e:
            logger.error(f"An error occurred: {e} 😢")

    asyncio.run(main())
