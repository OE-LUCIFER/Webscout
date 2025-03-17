import requests
import os
import uuid
import time
from typing import List, Optional, Union
from pathlib import Path
from requests.exceptions import RequestException

from webscout.AIbase import ImageProvider
from webscout.litagent import LitAgent

agent = LitAgent()

class MagicStudioImager(ImageProvider):
    """Your go-to provider for generating fire images with MagicStudio! 🎨"""
    
    def __init__(self, timeout: int = 60, proxies: dict = {}):
        """Initialize your MagicStudio provider with custom settings! ⚙️"""
        self.api_endpoint = "https://ai-api.magicstudio.com/api/ai-art-generator"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": agent.random(),
            "Origin": "https://magicstudio.com",
            "Referer": "https://magicstudio.com/ai-art-generator/",
            "DNT": "1",
            "Sec-GPC": "1"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
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
        """Generate some fire images from your prompt! 🎨"""
        if not prompt:
            raise ValueError("Yo fam, prompt can't be empty! 🚫")
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Amount needs to be a positive number! 📈")

        self.prompt = prompt
        response = []

        for _ in range(amount):
            form_data = {
                "prompt": prompt,
                "output_format": "bytes",
                "user_profile_id": "null",
                "anonymous_user_id": str(uuid.uuid4()),
                "request_timestamp": time.time(),
                "user_is_subscribed": "false",
                "client_id": uuid.uuid4().hex,
            }

            for attempt in range(max_retries):
                try:
                    resp = self.session.post(
                        self.api_endpoint,
                        data=form_data,
                        timeout=self.timeout
                    )
                    resp.raise_for_status()
                    response.append(resp.content)
                    break
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
        """Save your fire generated images! 💾"""
        save_dir = dir if dir else os.getcwd()
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        name = self.prompt if name is None else name
        filenames = []
        count = 0

        for image in response:
            def complete_path():
                count_value = "" if count == 0 else f"_{count}"
                return os.path.join(save_dir, filenames_prefix + name + count_value + "." + self.image_extension)

            while os.path.isfile(complete_path()):
                count += 1

            filepath = complete_path()
            filenames.append(os.path.basename(filepath))

            with open(filepath, "wb") as fh:
                fh.write(image)

        return filenames
