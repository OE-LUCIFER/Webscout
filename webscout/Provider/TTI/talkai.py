import uuid
import requests
import json
import os
from typing import Any, Dict, List, Optional

from webscout.AIbase import ImageProvider
from webscout import exceptions


class TalkaiImager(ImageProvider):
    """
    Image provider for Talkai.info.
    """

    def __init__(self, timeout: int = 60, proxies: dict = {}):
        """Initializes the TalkaiImager class.

        Args:
            timeout (int, optional): HTTP request timeout in seconds. Defaults to 60.
            proxies (dict, optional): HTTP request proxies. Defaults to {}.
        """
        self.api_endpoint = "https://talkai.info/chat/send/"
        self.headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://talkai.info',
            'referer': 'https://talkai.info/image/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"

    def generate(self, prompt: str, amount: int = 1) -> List[str]:
        """Generates image URLs from a prompt."""
        assert bool(prompt), "Prompt cannot be empty."
        assert isinstance(amount, int) and amount > 0, "Amount must be a positive integer."

        self.prompt = prompt
        image_urls = []

        try:
            with self.session.post(self.api_endpoint, json=self._create_payload(prompt), timeout=self.timeout) as response:
                response.raise_for_status()
                data = response.json()

                if 'data' in data and len(data['data']) > 0 and 'url' in data['data'][0]:
                    image_urls.append(data['data'][0]['url'])
                else:
                    raise exceptions.InvalidResponseError("No image URL found in API response.")

        except requests.exceptions.RequestException as e:
            raise exceptions.APIConnectionError(f"Error making API request: {e}") from e
        except json.JSONDecodeError as e:
            raise exceptions.InvalidResponseError(f"Invalid JSON response: {e}") from e
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"An unexpected error occurred: {e}") from e

        return image_urls

    def _create_payload(self, prompt: str) -> Dict[str, Any]:
        return {
            "type": "image",
            "messagesHistory": [
                {
                    "id": str(uuid.uuid4()),
                    "from": "you",
                    "content": prompt
                }
            ],
            "settings": {
                "model": "gpt-4o-mini"  # Or another suitable model if available
            }
        }


    def save(
        self,
        response: List[str],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        assert isinstance(response, list), f"Response should be a list, not {type(response)}"
        name = self.prompt if name is None else name

        filenames = []
        for i, url in enumerate(response):
            try:
                with self.session.get(url, stream=True, timeout=self.timeout) as r:
                    r.raise_for_status()
                    filename = f"{filenames_prefix}{name}_{i}.{self.image_extension}"
                    filepath = os.path.join(dir, filename)
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    filenames.append(filename)
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image from {url}: {e}")
                filenames.append(None) # Indicate failure to download

        return filenames


if __name__ == "__main__":
    bot = TalkaiImager()
    try:
        resp = bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
        print(bot.save(resp))
    except Exception as e:
        print(f"An error occurred: {e}")
