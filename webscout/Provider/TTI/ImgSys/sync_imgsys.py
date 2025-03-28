"""ImgSys Synchronous Provider - Generate images from multiple providers! 🔥

Examples:
    >>> from webscout import ImgSys
    >>> provider = ImgSys()
    >>> 
    >>> # Generate images
    >>> images = provider.generate("A cool cyberpunk city at night")
    >>> provider.save(images, dir="my_images")
"""

import requests
import os
import time
from typing import List, Optional, Union
from requests.exceptions import RequestException
from pathlib import Path

from webscout.AIbase import ImageProvider
from webscout.litagent import LitAgent

# Get a fresh user agent! 🔄
agent = LitAgent()

class ImgSys(ImageProvider):
    """Your homie for generating fire images using imgsys.org! 🎨

    This provider generates images from multiple providers, with built-in retry logic
    and error handling to make sure you get your images no cap! 💯

    Examples:
        >>> provider = ImgSys()
        >>> # Generate images
        >>> images = provider.generate("A futuristic city")
        >>> provider.save(images, "city.jpg")
    """

    def __init__(
        self, 
        timeout: int = 60, 
        proxies: Optional[dict] = None
    ):
        """Initialize your ImgSys provider with custom settings

        Examples:
            >>> provider = ImgSys(timeout=30)
            >>> provider = ImgSys(proxies={"http": "http://proxy:8080"})

        Args:
            timeout (int): HTTP request timeout in seconds (default: 60)
            proxies (dict, optional): Proxy configuration for requests
        """
        self.request_id_endpoint = "https://imgsys.org/api/initiate"
        self.image_response_endpoint = "https://imgsys.org/api/get"
        self.image_provider_endpoint = "https://imgsys.org/api/submit"
        
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": agent.random(),
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
            
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "jpeg"

    def generate(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: int = 5,
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Args:
            prompt (str): Your image description
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

        self.prompt = prompt
        response = []
        
        # Get request ID
        data = {"prompt": prompt}
        resp = self.session.post(self.request_id_endpoint, json=data, timeout=self.timeout)
        resp.raise_for_status()
        request_id = resp.json()["requestId"]

        # Poll for results
        for attempt in range(max_retries):
            try:
                # Get image URLs
                resp = self.session.get(
                    f"{self.image_response_endpoint}?requestId={request_id}",
                    timeout=self.timeout
                )
                resp.raise_for_status()
                image_data = resp.json()

                if "results" in image_data and len(image_data["results"]) >= 2:
                    # Get provider names
                    provider_resp = self.session.post(
                        self.image_provider_endpoint,
                        json={"requestId": request_id, "preference": 0},
                        timeout=self.timeout
                    )
                    provider_resp.raise_for_status()
                    provider_data = provider_resp.json()

                    # Download images
                    for i, url in enumerate(image_data["results"][:2]):
                        img_resp = self.session.get(url, timeout=self.timeout)
                        img_resp.raise_for_status()
                        response.append(img_resp.content)
                    
                    break
                else:
                    if attempt == max_retries - 1:
                        raise RequestException("Failed to get image results after max retries")
                    time.sleep(retry_delay)

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
            >>> provider = ImgSys()
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
        
        for i, image_bytes in enumerate(response):
            if name:
                filename = f"{filenames_prefix}{name}_{i}.{self.image_extension}"
            else:
                filename = f"{filenames_prefix}imgsys_{timestamp}_{i}.{self.image_extension}"
            
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            saved_paths.append(filepath)

        return saved_paths 