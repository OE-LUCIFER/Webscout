import requests
import json
import os
import time
from typing import List, Optional, Union
from pathlib import Path
from requests.exceptions import RequestException

from webscout.AIbase import ImageProvider
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent import LitAgent

# Initialize our fire logger and agent 🔥
logger = LitLogger(
    "Nexra",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK
)
agent = LitAgent()

class NexraImager(ImageProvider):
    """Your go-to provider for generating fire images with Nexra! 🔥

    Examples:
        >>> # Basic usage
        >>> provider = NexraImager()
        >>> images = provider.generate("Cool art")
        >>> paths = provider.save(images)
        >>>
        >>> # Advanced usage
        >>> provider = NexraImager(timeout=120)
        >>> images = provider.generate(
        ...     prompt="Epic dragon",
        ...     model="midjourney",
        ...     additional_params={
        ...         "data": {
        ...             "steps": 30,
        ...             "cfg_scale": 8
        ...         }
        ...     }
        ... )
        >>> paths = provider.save(images, name="dragon", dir="my_art")
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
        """Initialize your Nexra provider with custom settings! ⚙️

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
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = logging
        if self.logging:
            logger.info("Nexra provider initialized! 🚀")

    def generate(
        self,
        prompt: str,
        model: str = "midjourney",
        amount: int = 1,
        max_retries: int = 3,
        retry_delay: int = 5,
        additional_params: Optional[dict] = None
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Examples:
            >>> provider = NexraImager()
            >>> # Basic usage
            >>> images = provider.generate("Cool art")
            >>> # Advanced usage
            >>> images = provider.generate(
            ...     prompt="Epic dragon",
            ...     model="midjourney",
            ...     amount=3,
            ...     additional_params={"data": {"steps": 30}}
            ... )

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
            RequestException: If the API calls fail after retries
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

        if self.logging:
            logger.info(f"Generating {amount} images with {model}... 🎨")
        for attempt in range(max_retries):
            try:
                resp = self.session.post(self.url, json=payload, timeout=self.timeout)
                resp.raise_for_status()

                # Remove leading underscores and then parse JSON
                response_data = json.loads(resp.text.lstrip("_"))

                if response_data.get("status") and "images" in response_data:
                    for image_url in response_data["images"]:
                        img_resp = requests.get(image_url)
                        img_resp.raise_for_status()
                        response.append(img_resp.content)
                    if self.logging:
                        logger.success("Images generated successfully! 🎉")
                    break
                else:
                    raise Exception("Failed to generate image: " + str(response_data))
            except json.JSONDecodeError as json_err:
                if self.logging:
                    logger.error(f"JSON Decode Error: {json_err} 😢")
                    logger.debug(f"Raw response: {resp.text}")
                if attempt == max_retries - 1:
                    raise
            except RequestException as e:
                if self.logging:
                    logger.error(f"Failed to generate images: {e} 😢")
                if attempt == max_retries - 1:
                    raise
            if self.logging:
                logger.warning(f"Retrying in {retry_delay} seconds... 🔄")
            time.sleep(retry_delay)

        return response

    def save(
        self,
        response: List[bytes],
        name: Optional[str] = None,
        dir: Optional[Union[str, Path]] = None,
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire generated images! 💾

        Examples:
            >>> provider = NexraImager()
            >>> images = provider.generate("Cool art")
            >>> # Save with default settings
            >>> paths = provider.save(images)
            >>> # Save with custom name and directory
            >>> paths = provider.save(
            ...     images,
            ...     name="my_art",
            ...     dir="my_images",
            ...     filenames_prefix="test_"
            ... )

        Args:
            response (List[bytes]): Your generated images
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
        filenames = []

        if self.logging:
            logger.info(f"Saving {len(response)} images... 💾")
        for i, image in enumerate(response):
            filename = f"{filenames_prefix}{name}_{i}.{self.image_extension}"
            filepath = os.path.join(save_dir, filename)

            with open(filepath, "wb") as fh:
                fh.write(image)
            filenames.append(filename)
            if self.logging:
                logger.success(f"Saved image to: {filepath} 💾")

        if self.logging:
            logger.success(f"Images saved successfully! Check {dir} 🎉")
        return filenames

if __name__ == "__main__":
    bot = NexraImager()
    try:
        resp = bot.generate("A shiny red sports car speeding down a scenic mountain road", "midjourney")
        print(bot.save(resp))
    except Exception as e:
        logger.error(f"An error occurred: {e} 😢")
