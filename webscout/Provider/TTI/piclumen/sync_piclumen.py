"""PiclumenImager Synchronous Provider - Your go-to for high-quality AI art! 🔥

Examples:
    >>> from webscout import PiclumenImager
    >>> provider = PiclumenImager()
    >>> 
    >>> # Generate a single image
    >>> images = provider.generate("A cool cyberpunk city at night")
    >>> provider.save(images, dir="my_images")
    >>> 
    >>> # Generate multiple images with different settings
    >>> images = provider.generate(
    ...     prompt="An underwater alien creature with bioluminescent features", 
    ...     amount=3
    ... )
    >>> provider.save(images, dir="creatures")
"""

import requests
import os
import time
import json
from typing import List, Optional, Union
from datetime import datetime
from pathlib import Path
from requests.exceptions import RequestException

from webscout.AIbase import ImageProvider
from webscout.litagent import LitAgent

# Get a fresh user agent! 🔄
agent = LitAgent()

class PiclumenImager(ImageProvider):
    """Your homie for generating fire images using Piclumen! 🎨

    This provider generates high-quality AI art with built-in retry logic
    and error handling to make sure you get your images no cap! 💯

    Examples:
        >>> provider = PiclumenImager()
        >>> # Generate one image
        >>> image = provider.generate("A futuristic city")
        >>> provider.save(image, "city.jpg")
        >>> 
        >>> # Generate multiple images
        >>> images = provider.generate(
        ...     prompt="Underwater alien creatures",
        ...     amount=3
        ... )
        >>> provider.save(images, dir="ocean_creatures")
    """

    def __init__(
        self, 
        timeout: int = 120, 
        proxies: Optional[dict] = None
    ):
        """Initialize your PiclumenImager provider with custom settings

        Examples:
            >>> provider = PiclumenImager(timeout=180)
            >>> provider = PiclumenImager(proxies={"http": "http://proxy:8080"})

        Args:
            timeout (int): HTTP request timeout in seconds (default: 120)
            proxies (dict, optional): Proxy configuration for requests
        """
        self.api_endpoint = "https://s9.piclumen.art/comfy/api/generate-image"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://www.piclumen.com",
            "Referer": "https://s9.piclumen.art/",
            "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Gpc": "1",
            "User-Agent": agent.random(),  # Using our fire random agent! 🔥
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
            
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "jpg"

    def generate(
        self,
        prompt: str,
        amount: int = 1,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Args:
            prompt (str): Your image description
            amount (int): How many images you want (default: 1)
            max_retries (int): Max retry attempts if something fails (default: 3)
            retry_delay (int): Seconds to wait between retries (default: 5)

        Returns:
            List[bytes]: Your generated images as bytes

        Raises:
            ValueError: If the inputs ain't valid
            RequestException: If the API calls fail after retries
        """
        # Input validation
        if not prompt:
            raise ValueError("Yo fam, the prompt can't be empty! 🤔")
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Amount needs to be a positive number! 📈")

        self.prompt = prompt
        response = []
        
        # Payload with the prompt
        payload = {
            "prompt": prompt
        }

        for i in range(amount):
            for attempt in range(max_retries):
                try:
                    resp = self.session.post(
                        self.api_endpoint, 
                        json=payload,
                        timeout=self.timeout
                    )
                    resp.raise_for_status()
                    
                    # Check if response is an image
                    if resp.headers.get('content-type') == 'image/jpeg':
                        response.append(resp.content)
                        break
                    else:
                        if attempt == max_retries - 1:
                            raise RequestException(f"API returned non-image content: {resp.text[:100]}")
                
                except RequestException as e:
                    if attempt == max_retries - 1:
                        raise
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
            >>> provider = PiclumenImager()
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

        saved_paths = []
        timestamp = int(time.time())
        
        # Clean up name for filename use
        safe_name = ""
        if name:
            safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
            
        # Use prompt-based name if no name is provided
        if not safe_name and self.prompt:
            # Clean and truncate prompt for filename
            prompt_words = self.prompt.split()[:5]  # First 5 words
            safe_name = "_".join("".join(c if c.isalnum() else "_" for c in word) for word in prompt_words).lower()
        
        for i, image_bytes in enumerate(response):
            if safe_name:
                filename = f"{filenames_prefix}{safe_name}_{i}.{self.image_extension}"
            else:
                filename = f"{filenames_prefix}piclumen_{timestamp}_{i}.{self.image_extension}"
            
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            saved_paths.append(filepath)

        return saved_paths


if __name__ == "__main__":
    # Example usage
    provider = PiclumenImager()
    try:
        images = provider.generate(
            prompt="underwater macro photography, alien-like sea creature, translucent body, feathery appendages, glowing orbs, bioluminescent, ethereal, surreal",
            amount=1
        )
        paths = provider.save(images, dir="generated_images")
        print(f"Successfully saved images to: {paths}")
    except Exception as e:
        print(f"Oops, something went wrong: {e}")