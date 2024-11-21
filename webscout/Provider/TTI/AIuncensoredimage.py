import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

from webscout.AIbase import ImageProvider
from webscout import exceptions


class AIUncensoredImager(ImageProvider):
    """
    Image provider for AIUncensored.info.
    """

    def __init__(self, timeout: int = 60, proxies: dict = {}):
        """Initializes the AIUncensoredImager class."""
        self.url = "https://twitterclone-i0wr.onrender.com/api/image"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://www.aiuncensored.info",
            "Referer": "https://www.aiuncensored.info/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt = "AI-generated image - webscout"
        self.image_extension = "jpg"

    def generate(self, prompt: str, amount: int = 1) -> List[str]:
        """Generates image URLs from a prompt."""

        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int) and amount > 0, "Amount must be a positive integer"
        self.prompt = prompt

        payload = {"prompt": prompt}
        image_urls = []

        try:
            with self.session.post(self.url, json=payload, timeout=self.timeout) as response:
                response.raise_for_status()  # Raise HTTPError for bad responses
                data = response.json()
                image_url = data.get("image_url")

                if not image_url:
                    raise exceptions.InvalidResponseError("No image URL in API response")

                image_urls.append(image_url) # Only one image returned for now


        except requests.exceptions.RequestException as e:
            raise exceptions.APIConnectionError(f"Error during request: {e}")
        except json.JSONDecodeError as e:
            raise exceptions.InvalidResponseError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Unexpected error: {e}")

        return image_urls

    def save(
        self,
        response: List[str],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        """Saves generated images."""

        assert isinstance(response, list), f"Response should be a list, not {type(response)}"
        name = self.prompt if name is None else name
        os.makedirs(dir, exist_ok=True) #Create dir if needed

        filenames = []
        for i, img_url in enumerate(response):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{dir}/{name}_{i + 1}_{timestamp}.{self.image_extension}"
            filenames.append(filenames_prefix + os.path.basename(filename))

            try:
                with self.session.get(img_url, stream=True, timeout=self.timeout) as img_response:
                    img_response.raise_for_status()
                    with open(filename, "wb") as f:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            f.write(chunk)
            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToSaveImageError(f"Error downloading/saving image: {e}")

        return filenames


if __name__ == "__main__":
    imager = AIUncensoredImager()
    prompt = "a photo of a cat sitting in a basket"
    try:
        image_urls = imager.generate(prompt, amount=1)
        saved_filenames = imager.save(image_urls)
        print(f"Saved filenames: {saved_filenames}")
    except Exception as e:
        print(f"An error occurred: {e}")