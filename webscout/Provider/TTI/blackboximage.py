import requests
import json
import uuid
import os
import time
from typing import List
from requests.exceptions import RequestException

from webscout.AIbase import ImageProvider

class BlackboxAIImager(ImageProvider):
    """Image provider for Blackbox AI"""

    def __init__(self, timeout: int = 60, proxies: dict = {}):
        """Initializes the BlackboxAIImager class.

        Args:
            timeout (int, optional): HTTP request timeout in seconds. Defaults to 60.
            proxies (dict, optional): HTTP request proxies. Defaults to {}.
        """
        self.url = "https://www.blackbox.ai/api/chat"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
            "Origin": "https://www.blackbox.ai",
            "Referer": "https://www.blackbox.ai/agent/ImageGenerationLV45LJp"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "jpg"

    def generate(
        self, prompt: str, amount: int = 1,
        max_retries: int = 3, retry_delay: int = 5
    ) -> List[bytes]:
        """Generate image from prompt

        Args:
            prompt (str): Image description.
            amount (int): Total images to be generated. Defaults to 1.
            max_retries (int, optional): Maximum number of retry attempts. Defaults to 3.
            retry_delay (int, optional): Delay between retries in seconds. Defaults to 5.

        Returns:
            List[bytes]: List of generated images as bytes.
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"

        self.prompt = prompt
        response = []

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
                    break
                except RequestException as e:
                    if attempt == max_retries - 1:
                        print(f"Failed to generate image after {max_retries} attempts: {e}")
                        raise
                    else:
                        print(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)

        return response

    def save(
        self,
        response: List[bytes],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save generated images

        Args:
            response (List[bytes]): List of generated images as bytes.
            name (str): Filename for the images. Defaults to the last prompt.
            dir (str, optional): Directory for saving images. Defaults to os.getcwd().
            filenames_prefix (str, optional): String to be prefixed at each filename to be returned.

        Returns:
            List[str]: List of saved filenames.
        """
        assert isinstance(response, list), f"Response should be of {list} not {type(response)}"
        name = self.prompt if name is None else name

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

        return filenames

if __name__ == "__main__":
    bot = BlackboxAIImager()
    try:
        resp = bot.generate("AI-generated image - webscout", 1)
        print(bot.save(resp))
    except Exception as e:
        print(f"An error occurred: {e}")