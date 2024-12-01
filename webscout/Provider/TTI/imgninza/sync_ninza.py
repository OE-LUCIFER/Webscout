import requests
import json
import os
from typing import List, Dict, Optional

from webscout.AIbase import ImageProvider
from webscout import exceptions
from webscout.litagent import agent  # Import our fire user agent generator 🔥
from webscout.Litlogger import LitLogger  # For that cyberpunk logging swag ⚡

# Initialize our fire logger 🚀
logger = LitLogger("NinjaImager", "MODERN_EMOJI")

class NinjaImager(ImageProvider):
    """
    Image provider for NinjaChat.ai - Your go-to for fire AI art! 🎨
    
    >>> # Generate some fire art! 🔥
    >>> imager = NinjaImager(logging=True)
    >>> images = imager.generate("Epic dragon breathing fire", amount=2)
    >>> paths = imager.save(images)
    >>> print(paths)
    ['epic_dragon_0.png', 'epic_dragon_1.png']
    
    >>> # Turn off logging for stealth mode 🥷
    >>> quiet_imager = NinjaImager(logging=False)
    >>> images = quiet_imager.generate("Cyberpunk city at night")
    >>> paths = quiet_imager.save(images)
    """

    AVAILABLE_MODELS = {
        "stable-diffusion": "https://www.ninjachat.ai/api/image-generator",
        "flux-dev": "https://www.ninjachat.ai/api/flux-image-generator",
    }

    def __init__(self, timeout: int = 60, proxies: dict = {}, logging: bool = True):
        """Initialize your NinjaChatImager with custom settings! ⚙️

        Args:
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://www.ninjachat.ai",
            "Priority": "u=1, i",
            "Referer": "https://www.ninjachat.ai/image-generation",
            "Sec-CH-UA": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": agent.random()  # Using our fire random agent! 🔥
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt = "AI-generated image - webscout"
        self.image_extension = "png"
        self.logging = logging
        if self.logging:
            logger.info("NinjaImager initialized! Ready to create some fire art! 🚀")

    def generate(self, prompt: str, amount: int = 1, model: str = "flux-dev") -> List[str]:
        """Generate some fire images from your prompt! 🎨

        Args:
            prompt (str): Your creative prompt
            amount (int): How many images to generate
            model (str): Which model to use (default: flux-dev)

        Returns:
            List[str]: URLs to your generated images
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int) and amount > 0, "Amount should be a positive integer"

        if model not in self.AVAILABLE_MODELS:
            raise exceptions.ModelNotFoundError(
                f"Model '{model}' not found. Available models: {', '.join(self.AVAILABLE_MODELS)}"
            )

        self.prompt = prompt
        url = self.AVAILABLE_MODELS[model]

        payload = {
            "prompt": prompt,
            "model": model if model == "flux-dev" else "stable-diffusion",
            "negativePrompt": "",
            "cfg": 7,
            "aspectRatio": "1:1",
            "outputFormat": self.image_extension,
            "numOutputs": amount,
            "outputQuality": 90
        }

        if self.logging:
            logger.info(f"Generating {amount} images with {model}... 🎨")

        image_urls = []
        try:
            with requests.post(url, headers=self.headers, json=payload, timeout=self.timeout) as response:
                if response.status_code != 200:
                    if self.logging:
                        logger.error(f"Request failed with status {response.status_code} 😢")
                    raise exceptions.FailedToGenerateResponseError(
                        f"Request failed with status code: {response.status_code}, {response.text}"
                    )

                data = response.json()

                if 'output' not in data:
                    if self.logging:
                        logger.error("Invalid API response format 😢")
                    raise exceptions.InvalidResponseError("Invalid API response format: 'output' key missing.")

                for img_url in data['output']:
                    image_urls.append(img_url)
                    if self.logging:
                        logger.success(f"Generated image {len(image_urls)}/{amount}! 🎨")

        except requests.exceptions.RequestException as e:
            if self.logging:
                logger.error(f"Connection error: {e} 😢")
            raise exceptions.APIConnectionError(f"An error occurred during the request: {e}")
        except json.JSONDecodeError as e:
            if self.logging:
                logger.error(f"Failed to parse response: {e} 😢")
            raise exceptions.InvalidResponseError(f"Failed to parse JSON response: {e}")

        if self.logging:
            logger.success("All images generated successfully! 🎉")
        return image_urls

    def save(
        self,
        response: List[str],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire images! 💾

        Args:
            response (List[str]): List of image URLs
            name (str, optional): Base name for saved files
            dir (str, optional): Where to save the images
            filenames_prefix (str, optional): Prefix for filenames

        Returns:
            List[str]: List of saved filenames
        """
        assert isinstance(response, list), f"Response should be a list, not {type(response)}"
        name = self.prompt if name is None else name

        if not os.path.exists(dir):
            os.makedirs(dir)
            if self.logging:
                logger.info(f"Created directory: {dir} 📁")

        if self.logging:
            logger.info(f"Saving {len(response)} images... 💾")

        filenames = []
        count = 0
        for img_url in response:
            def complete_path():
                count_value = "" if count == 0 else f"_{count}"
                return os.path.join(dir, name + count_value + "." + self.image_extension)

            while os.path.isfile(complete_path()):
                count += 1

            absolute_path_to_file = complete_path()
            filenames.append(filenames_prefix + os.path.split(absolute_path_to_file)[1])

            try:
                with requests.get(img_url, stream=True, timeout=self.timeout) as img_response:
                    img_response.raise_for_status()
                    with open(absolute_path_to_file, "wb") as f:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    if self.logging:
                        logger.success(f"Saved image to: {absolute_path_to_file} 💾")

            except requests.exceptions.RequestException as e:
                if self.logging:
                    logger.error(f"Failed to save image: {e} 😢")
                raise exceptions.FailedToSaveImageError(f"An error occurred while downloading/saving image: {e}")

        if self.logging:
            logger.success(f"All images saved successfully! Check {dir} 🎉")
        return filenames


if __name__ == "__main__":
    bot = NinjaImager()
    try:
        resp = bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
        print(bot.save(resp))
    except Exception as e:
        print(f"An error occurred: {e}")
