"""
HFimager - Your go-to provider for generating fire images with HuggingFace! 🔥

Examples:
    >>> from webscout import HFimager
    >>> 
    >>> # Initialize with your API key
    >>> provider = HFimager(api_token="your-hf-token")
    >>> 
    >>> # Generate a single image
    >>> images = provider.generate("A shiny red sports car", model="stabilityai/stable-diffusion-xl-base-1.0")
    >>> paths = provider.save(images)
    >>> 
    >>> # Generate multiple images with parameters
    >>> images = provider.generate(
    ...     prompt="Epic dragon in cyberpunk city",
    ...     amount=3,
    ...     model="runwayml/stable-diffusion-v1-5",
    ...     guidance_scale=7.5,
    ...     negative_prompt="blurry, bad quality",
    ...     num_inference_steps=50,
    ...     width=768,
    ...     height=768
    ... )
    >>> paths = provider.save(images, name="dragon", dir="outputs")
"""

import os
import requests
import io
from PIL import Image
from typing import Any, List, Optional, Dict
from webscout.AIbase import ImageProvider
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent import LitAgent

# Initialize our fire logger and agent 🔥
logger = LitLogger(
    "HuggingFace",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK
)
agent = LitAgent()

class HFimager(ImageProvider):
    """Your go-to provider for generating fire images with HuggingFace! 🔥"""

    def __init__(
        self,
        api_token: str = None,
        timeout: int = 60,
        proxies: dict = {},
        logging: bool = True
    ):
        """Initialize your HuggingFace provider with custom settings! ⚙️

        Args:
            api_token (str, optional): HuggingFace API token. Uses env var "HUGGINGFACE_API_TOKEN" if None
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.base_url = "https://api-inference.huggingface.co/models/"
        self.api_token = api_token or os.environ["HUGGINGFACE_API_TOKEN"]
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "User-Agent": agent.random(),
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "jpg"
        self.logging = logging
        if self.logging:
            logger.info("HuggingFace provider initialized! 🚀")

    def generate(
        self,
        prompt: str,
        amount: int = 1,
        model: str = "stabilityai/stable-diffusion-xl-base-1.0",
        guidance_scale: Optional[float] = None,
        negative_prompt: Optional[str] = None,
        num_inference_steps: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        scheduler: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> List[bytes]:
        """Generate some fire images! 🎨

        Args:
            prompt (str): Your lit image description
            amount (int): How many images to generate (default: 1)
            model (str): Which model to use (default: "stabilityai/stable-diffusion-xl-base-1.0")
            guidance_scale (float, optional): Control how much to follow your prompt
            negative_prompt (str, optional): What you don't want in the image
            num_inference_steps (int, optional): More steps = better quality but slower
            width (int, optional): Image width
            height (int, optional): Image height
            scheduler (str, optional): Which scheduler to use
            seed (int, optional): Random seed for reproducibility

        Returns:
            List[bytes]: Your generated images as bytes
        """
        assert bool(prompt), "Yo fam, prompt can't be empty! 🚫"
        assert isinstance(amount, int), f"Amount gotta be an integer, not {type(amount)} 🤔"
        assert amount > 0, "Amount gotta be greater than 0! 📈"

        self.prompt = prompt
        response = []
        if self.logging:
            logger.info(f"Generating {amount} images with {model}... 🎨")

        for _ in range(amount):
            url = self.base_url + model
            payload: Dict[str, Any] = {"inputs": prompt}
            parameters = {}

            if guidance_scale is not None:
                parameters["guidance_scale"] = guidance_scale
            if negative_prompt is not None:
                parameters["negative_prompt"] = negative_prompt
            if num_inference_steps is not None:
                parameters["num_inference_steps"] = num_inference_steps
            if width is not None and height is not None:
                parameters["target_size"] = {"width": width, "height": height}
            if scheduler is not None:
                parameters["scheduler"] = scheduler
            if seed is not None:
                parameters["seed"] = seed

            if parameters:
                payload["parameters"] = parameters

            try:
                resp = self.session.post(url, headers=self.headers, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                response.append(resp.content)
                if self.logging:
                    logger.success("Image generated successfully! 🎉")
            except requests.RequestException as e:
                if self.logging:
                    logger.error(f"Failed to generate image: {e} 😢")
                raise

        return response

    def save(
        self,
        response: List[bytes],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire images! 💾

        Args:
            response (List[bytes]): Your generated images
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

        for image_bytes in response:
            def complete_path():
                count_value = "" if count == 0 else f"_{count}"
                return os.path.join(dir, name + count_value + "." + self.image_extension)

            while os.path.isfile(complete_path()):
                count += 1

            absolute_path_to_file = complete_path()
            filenames.append(filenames_prefix + os.path.split(absolute_path_to_file)[1])

            with open(absolute_path_to_file, "wb") as fh:
                fh.write(image_bytes)

        if self.logging:
            logger.success(f"Images saved successfully! Check {dir} 🎉")
        return filenames
