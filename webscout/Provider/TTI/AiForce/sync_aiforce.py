import requests
import os
import time
from typing import List, Optional, Union
from string import punctuation
from random import choice
from requests.exceptions import RequestException
from pathlib import Path

from webscout.AIbase import ImageProvider

from webscout.litagent import LitAgent


agent = LitAgent()

class AiForceimager(ImageProvider):
    """Your go-to provider for generating fire images with AiForce! 🔥

    Examples:
        >>> # Basic usage
        >>> provider = AiForceimager()
        >>> images = provider.generate("Cool art")
        >>> paths = provider.save(images)
        >>>
        >>> # Advanced usage
        >>> provider = AiForceimager(timeout=120)
        >>> images = provider.generate(
        ...     prompt="Epic dragon",
        ...     amount=3,
        ...     model="Flux-1.1-Pro",
        ...     width=1024,
        ...     height=1024
        ... )
        >>> paths = provider.save(images, name="dragon", dir="my_art")
    """

    AVAILABLE_MODELS = [
        "stable-diffusion-xl-lightning",
        "stable-diffusion-xl-base",
        "flux",
        "flux-realism",
        "flux-anime",
        "flux-3d",
        "flux-disney",
        "flux-pixel",
        "flux-4o",
        "any-dark"
    ]

    def __init__(self, timeout: int = 60, proxies: dict = {}):
        """Initialize your AiForce provider with custom settings! ⚙️

        Args:
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
        """
        self.api_endpoint = "https://api.airforce/imagine2"
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": agent.random()
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"


    def generate(
        self, 
        prompt: str, 
        amount: int = 1, 
        additives: bool = True,
        model: str = "flux-3d", 
        width: int = 768, 
        height: int = 768, 
        seed: Optional[int] = None,
        max_retries: int = 3, 
        retry_delay: int = 5
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Examples:
            >>> provider = AiForceimager()
            >>> # Basic usage
            >>> images = provider.generate("Cool art")
            >>> # Advanced usage
            >>> images = provider.generate(
            ...     prompt="Epic dragon",
            ...     amount=3,
            ...     model="Flux-1.1-Pro"
            ... )

        Args:
            prompt (str): Your image description
            amount (int): How many images you want (default: 1)
            additives (bool): Make each prompt unique (default: True)
            model (str): Model to use - check AVAILABLE_MODELS (default: "Flux-1.1-Pro")
            width (int): Image width (default: 768)
            height (int): Image height (default: 768)
            seed (int, optional): Seed for reproducible results
            max_retries (int): Max retry attempts if something fails (default: 3)
            retry_delay (int): Seconds to wait between retries (default: 5)

        Returns:
            List[bytes]: Your generated images

        Raises:
            ValueError: If the inputs ain't valid
            RequestException: If the API calls fail after retries
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"
        assert model in self.AVAILABLE_MODELS, f"Model should be one of {self.AVAILABLE_MODELS}"

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
        for _ in range(amount):
            url = f"{self.api_endpoint}?model={model}&prompt={prompt}&size={width}:{height}"
            if seed:
                url += f"&seed={seed}"
            
            for attempt in range(max_retries):
                try:
                    resp = self.session.get(url, timeout=self.timeout)
                    resp.raise_for_status()
                    response.append(resp.content)
                    break
                except RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    else:
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
            >>> provider = AiForceimager()
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
        filenames = []
        count = 0

        for image in response:
            def complete_path():
                count_value = "" if count == 0 else f"_{count}"
                return os.path.join(save_dir, name + count_value + "." + self.image_extension)

            while os.path.isfile(complete_path()):
                count += 1

            absolute_path_to_file = complete_path()
            filenames.append(filenames_prefix + os.path.split(absolute_path_to_file)[1])

            with open(absolute_path_to_file, "wb") as fh:
                fh.write(image)

        return filenames

if __name__ == "__main__":
    bot = AiForceimager()
    test_prompt = "A shiny red sports car speeding down a scenic mountain road"
    
    print(f"Testing all available models with prompt: '{test_prompt}'")
    print("-" * 50)
    
    # Create a directory for test images if it doesn't exist
    test_dir = "model_test_images"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        
    for model in bot.AVAILABLE_MODELS:
        print(f"Testing model: {model}")
        try:
            # Generate an image with the current model
            resp = bot.generate(
                prompt=test_prompt,
                amount=1,
                model=model,
                width=768,
                height=768
            )
            
            # Save the image with model name as prefix
            saved_paths = bot.save(
                resp, 
                name=f"{model}_test", 
                dir=test_dir, 
                filenames_prefix=f"{model}_"
            )
            
            print(f"✓ Success! Saved image: {saved_paths[0]}")
        except Exception as e:
            print(f"✗ Failed with model {model}: {str(e)}")
        
        print("-" * 30)
    
    print("All model tests completed!")
