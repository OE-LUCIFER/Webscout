import requests
import json
import uuid
import os
import time
from typing import List
from requests.exceptions import RequestException

from webscout.AIbase import ImageProvider
from webscout.litagent import LitAgent  # Import our fire user agent generator 🔥
from webscout.Litlogger import LitLogger  # For that cyberpunk logging swag ⚡

# Initialize our fire logger 🚀
logger = LitLogger("BlackboxAIImager")

class BlackboxAIImager(ImageProvider):
    """
    BlackboxAI Image Provider - Your go-to for fire AI art! 🎨
    
    >>> # Generate some fire art! 🔥
    >>> imager = BlackboxAIImager(logging=True)
    >>> images = imager.generate("Epic dragon breathing fire", amount=2)
    >>> paths = imager.save(images)
    >>> print(paths)
    ['epic_dragon_0.jpg', 'epic_dragon_1.jpg']
    
    >>> # Turn off logging for stealth mode 🥷
    >>> quiet_imager = BlackboxAIImager(logging=False)
    >>> images = quiet_imager.generate("Cyberpunk city at night")
    >>> paths = quiet_imager.save(images)
    """

    def __init__(self, timeout: int = 60, proxies: dict = {}, logging: bool = True):
        """Initialize your BlackboxAI provider with custom settings! ⚙️

        Args:
            timeout (int): Request timeout in seconds (default: 60)
            proxies (dict): Proxy settings for requests (default: {})
            logging (bool): Enable fire logging (default: True)
        """
        self.url = "https://www.blackbox.ai/api/chat"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": LitAgent().random(),  # Using our fire random agent! 🔥
            "Origin": "https://www.blackbox.ai",
            "Referer": "https://www.blackbox.ai/agent/ImageGenerationLV45LJp"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "jpg"
        self.logging = logging
        if self.logging:
            logger.info("BlackboxAIImager initialized! Ready to create some fire art! 🚀")

    def generate(
        self, prompt: str, amount: int = 1,
        max_retries: int = 3, retry_delay: int = 5
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Args:
            prompt (str): Your creative prompt
            amount (int): How many images to generate
            max_retries (int): Max retry attempts if generation fails
            retry_delay (int): Seconds to wait between retries

        Returns:
            List[bytes]: Your generated images as bytes
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"

        self.prompt = prompt
        response = []

        if self.logging:
            logger.info(f"Generating {amount} images... 🎨")

        for _ in range(amount):
            message_id = str(uuid.uuid4())
            payload = {
                "messages": [
                    {
                        "id": message_id,
                        "content": prompt,
                        "role": "user"
                    }
                ],
                "id": message_id,
                "previewToken": None,
                "userId": None,
                "codeModelMode": True,
                "agentMode": {
                    "mode": True,
                    "id": "ImageGenerationLV45LJp",
                    "name": "Image Generation"
                },
                "trendingAgentMode": {},
                "isMicMode": False,
                "maxTokens": 1024,
                "isChromeExt": False,
                "githubToken": None,
                "clickedAnswer2": False,
                "clickedAnswer3": False,
                "clickedForceWebSearch": False,
                "visitFromDelta": False,
                "mobileClient": False
            }

            for attempt in range(max_retries):
                try:
                    resp = self.session.post(self.url, json=payload, timeout=self.timeout)
                    resp.raise_for_status()
                    response_data = resp.text
                    image_url = response_data.split("(")[1].split(")")[0]
                    image_response = requests.get(image_url)
                    image_response.raise_for_status()
                    response.append(image_response.content)
                    if self.logging:
                        logger.success(f"Generated image {len(response)}/{amount}! 🎨")
                    break
                except RequestException as e:
                    if attempt == max_retries - 1:
                        if self.logging:
                            logger.error(f"Failed to generate image after {max_retries} attempts: {e} 😢")
                        raise
                    else:
                        if self.logging:
                            logger.warning(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds... 🔄")
                        time.sleep(retry_delay)

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
    bot = BlackboxAIImager()
    try:
        resp = bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
        print(bot.save(resp))
    except Exception as e:
        if bot.logging:
            logger.error(f"An error occurred: {e} 😢")
