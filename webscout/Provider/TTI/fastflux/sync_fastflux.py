"""FastFluxImager Synchronous Provider - Generate stunning AI art with FastFlux! 🎨

Examples:
    >>> from webscout import FastFluxImager
    >>> provider = FastFluxImager()
    >>> 
    >>> # Generate a single image
    >>> images = provider.generate("A cool cyberpunk city at night")
    >>> paths = provider.save(images, dir="my_images")
    >>> 
    >>> # Generate multiple images with different settings
    >>> images = provider.generate(
    ...     prompt="Epic dragon breathing fire",
    ...     amount=2, 
    ...     model="flux_1_schnell"
    ... )
    >>> provider.save(images, dir="dragon_pics")
"""

import requests
import base64
import json
import os
import time
from typing import List, Optional, Union
from requests.exceptions import RequestException
from pathlib import Path

from webscout.AIbase import ImageProvider
from webscout.litagent import LitAgent

# Get a fresh user agent! 🔄
agent = LitAgent()

class FastFluxImager(ImageProvider):
    """Your go-to provider for generating fire images with FastFlux! 🎨

    Examples:
        >>> provider = FastFluxImager()
        >>> # Generate one image with default model
        >>> image = provider.generate("A futuristic city")
        >>> provider.save(image, "city.png")
        >>> 
        >>> # Generate multiple images with specific model
        >>> images = provider.generate(
        ...     prompt="Space station",
        ...     amount=3,
        ...     model="flux_1_dev"
        ... )
        >>> provider.save(images, dir="space_pics")
    """

    AVAILABLE_MODELS = [
        "flux_1_schnell",  # Fast generation model (default)
        "flux_1_dev",      # Developer model
        "sana_1_6b"        # SANA 1.6B model
    ]

    AVAILABLE_SIZES = [
        "1_1",
        "16_9",
        "4_3",
    ]

    def __init__(self, timeout: int = 60, proxies: dict = None):
        """Initialize your FastFluxImager provider with custom settings

        Examples:
            >>> provider = FastFluxImager(timeout=120)
            >>> provider = FastFluxImager(proxies={"http": "http://proxy:8080"})

        Args:
            timeout (int): HTTP request timeout in seconds (default: 60)
            proxies (dict, optional): Proxy configuration for requests
            logging (bool): Enable/disable logging (default: True)
        """
        self.api_endpoint = "https://api.fastflux.co/v1/images/generate"
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://fastflux.co",
            "referer": "https://fastflux.co/",
            "user-agent": agent.random()
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = True

    def generate(
        self,
        prompt: str,
        amount: int = 1,
        model: str = "flux_1_schnell",
        size: str = "1_1",
        is_public: bool = False,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Examples:
            >>> provider = FastFluxImager()
            >>> # Basic usage
            >>> images = provider.generate("Cool art")
            >>> # Advanced usage
            >>> images = provider.generate(
            ...     prompt="Epic dragon",
            ...     amount=2,
            ...     model="flux_1_dev",
            ...     size="16_9"
            ... )

        Args:
            prompt (str): Your image description
            amount (int): How many images you want (default: 1)
            model (str): Model to use - check AVAILABLE_MODELS (default: "flux_1_schnell")
            size (str): Image size ratio (default: "1_1")
            is_public (bool): Whether to make the image public (default: False)
            max_retries (int): Max retry attempts if something fails (default: 3)
            retry_delay (int): Seconds to wait between retries (default: 5)

        Returns:
            List[bytes]: Your generated images

        Raises:
            ValueError: If the inputs ain't valid
            RequestException: If the API calls fail after retries
        """
        if not prompt:
            raise ValueError("Yo fam, the prompt can't be empty! 🤔")
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Amount needs to be a positive number! 📈")
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model must be one of {self.AVAILABLE_MODELS}! 🎯")
        if size not in self.AVAILABLE_SIZES:
            raise ValueError(f"Size must be one of {self.AVAILABLE_SIZES}! 📏")

        self.prompt = prompt
        response = []

        # Prepare payload
        payload = {
            "prompt": prompt,
            "model": model,
            "size": size,
            "isPublic": is_public
        }

        for i in range(amount):
            for attempt in range(max_retries):
                try:
                    if self.logging:
                        print(f"Generating image {i+1}/{amount}... 🎨")
                    
                    resp = self.session.post(
                        self.api_endpoint,
                        json=payload,
                        timeout=self.timeout
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    
                    if result and 'result' in result:
                        # Get base64 data and remove header
                        image_data = result['result']
                        base64_data = image_data.split(',')[1]
                        
                        # Decode base64 data
                        image_bytes = base64.b64decode(base64_data)
                        response.append(image_bytes)

                        break
                    else:
                        raise RequestException("Invalid response format")
                        
                except RequestException as e:
                    if attempt == max_retries - 1:
                        raise RequestException(f"Failed to generate image after {max_retries} attempts: {e}")

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
            >>> provider = FastFluxImager()
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

        name = self.prompt if name is None else name
        
        # Clean up name for filename use
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
        safe_name = safe_name[:50]  # Truncate if too long
        
        filenames = []

        for i, image in enumerate(response):
            filename = f"{filenames_prefix}{safe_name}_{i}.{self.image_extension}"
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(image)
            
            filenames.append(filename)

        return filenames


if __name__ == "__main__":
    # Example usage
    provider = FastFluxImager()
    try:
        images = provider.generate("A cyberpunk city at night with neon lights", amount=1)
        paths = provider.save(images, dir="generated_images")
        print(f"Successfully saved images to: {paths}")
    except Exception as e:
        print(f"Oops, something went wrong: {e}")
