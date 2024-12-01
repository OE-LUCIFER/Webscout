import requests
import os
from typing import List
from string import punctuation
from random import choice
from random import randint
import base64

from webscout.AIbase import ImageProvider
from webscout.litagent import LitAgent  # Import our fire user agent generator 🔥
from webscout.Litlogger import LitLogger  # For that cyberpunk logging swag ⚡

# Initialize our fire logger 🚀
logger = LitLogger("DeepInfraImager")

class DeepInfraImager(ImageProvider):
    """
    DeepInfra Image Provider - Your go-to for fire AI art! 🎨
    
    >>> # Generate some fire art! 🔥
    >>> imager = DeepInfraImager(logging=True)
    >>> images = imager.generate("Epic dragon breathing fire", amount=2)
    >>> paths = imager.save(images)
    >>> print(paths)
    ['epic_dragon_0.png', 'epic_dragon_1.png']
    
    >>> # Turn off logging for stealth mode 🥷
    >>> quiet_imager = DeepInfraImager(logging=False)
    >>> images = quiet_imager.generate("Cyberpunk city at night")
    >>> paths = quiet_imager.save(images)
    """

    def __init__(
        self,
        model: str = "black-forest-labs/FLUX-1-schnell",
        timeout: int = 60,
        proxies: dict = {},
        logging: bool = True
    ):
        """Initialize your DeepInfra provider with custom settings! ⚙️

        Args:
            model (str): Which model to use (default: black-forest-labs/FLUX-1-schnell)
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.image_gen_endpoint: str = f"https://api.deepinfra.com/v1/inference/{model}"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": LitAgent().random(),  # Using our fire random agent! 🔥
            "DNT": "1",
            "Origin": "https://deepinfra.com",
            "Referer": "https://deepinfra.com/",
            "Sec-CH-UA": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = logging
        if self.logging:
            logger.info("DeepInfraImager initialized! Ready to create some fire art! 🚀")

    def generate(
        self, prompt: str, amount: int = 1, additives: bool = True, 
        num_inference_steps: int = 25, guidance_scale: float = 7.5, 
        width: int = 1024, height: int = 1024, seed: int = None
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Args:
            prompt (str): Your creative prompt
            amount (int): How many images to generate
            additives (bool): Add random characters to make prompts unique
            num_inference_steps (int): Number of inference steps
            guidance_scale (float): Guidance scale for generation
            width (int): Image width
            height (int): Image height
            seed (int, optional): Random seed for reproducibility

        Returns:
            List[bytes]: Your generated images as bytes
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"

        ads = lambda: (
            ""
            if not additives
            else choice(punctuation)
            + choice(punctuation)
            + choice(punctuation)
            + choice(punctuation)
            + choice(punctuation)
        )

        if self.logging:
            logger.info(f"Generating {amount} images... 🎨")

        self.prompt = prompt
        response = []
        for _ in range(amount):
            payload = {
                "prompt": prompt + ads(),
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "width": width,
                "height": height,
                "seed": seed if seed is not None else randint(1, 10000), 
            }
            try:
                resp = self.session.post(url=self.image_gen_endpoint, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                # Extract base64 encoded image data and decode it
                image_data = resp.json()['images'][0].split(",")[1]
                image_bytes = base64.b64decode(image_data)
                response.append(image_bytes)
                if self.logging:
                    logger.success(f"Generated image {len(response)}/{amount}! 🎨")
            except Exception as e:
                if self.logging:
                    logger.error(f"Failed to generate image: {e} 😢")
                raise

        if self.logging:
            logger.success("All images generated successfully! 🎉")
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
            response (List[bytes]): List of image data
            name (str, optional): Base name for saved files
            dir (str, optional): Where to save the images
            filenames_prefix (str, optional): Prefix for filenames

        Returns:
            List[str]: List of saved filenames
        """
        assert isinstance(response, list), f"Response should be of {list} not {type(response)}"
        name = self.prompt if name is None else name

        if not os.path.exists(dir):
            os.makedirs(dir)
            if self.logging:
                logger.info(f"Created directory: {dir} 📁")

        if self.logging:
            logger.info(f"Saving {len(response)} images... 💾")

        filenames = []
        count = 0
        for image in response:
            def complete_path():
                count_value = "" if count == 0 else f"_{count}"
                return os.path.join(dir, name + count_value + "." + self.image_extension)

            while os.path.isfile(complete_path()):
                count += 1

            absolute_path_to_file = complete_path()
            filenames.append(filenames_prefix + os.path.split(absolute_path_to_file)[1])

            with open(absolute_path_to_file, "wb") as fh:
                fh.write(image)
            if self.logging:
                logger.success(f"Saved image to: {absolute_path_to_file} 💾")

        if self.logging:
            logger.success(f"All images saved successfully! Check {dir} 🎉")
        return filenames


if __name__ == "__main__":
    bot = DeepInfraImager()
    try:
        resp = bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
        print(bot.save(resp))
    except Exception as e:
        if bot.logging:
            logger.error(f"An error occurred: {e} 😢")
