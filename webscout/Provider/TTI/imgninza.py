import requests
import json
import os
from typing import List, Dict, Optional

from webscout.AIbase import ImageProvider
from webscout import exceptions  # Import exceptions module


class NinjaImager(ImageProvider):
    """
    Image provider for NinjaChat.ai.
    """

    AVAILABLE_MODELS = {
        "stable-diffusion": "https://www.ninjachat.ai/api/image-generator",
        "flux-dev": "https://www.ninjachat.ai/api/flux-image-generator",
    }

    def __init__(self, timeout: int = 60, proxies: dict = {}):
        """Initializes the NinjaChatImager class."""
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt = "AI-generated image - webscout"
        self.image_extension = "png"  # Default extension

    def generate(self, prompt: str, amount: int = 1, model: str = "flux-dev") -> List[str]:
        """Generate images from a prompt."""

        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int) and amount > 0, "Amount should be a positive integer"

        if model not in self.AVAILABLE_MODELS:
            raise exceptions.ModelNotFoundError(f"Model '{model}' not found. Available models: {', '.join(self.AVAILABLE_MODELS)}")

        self.prompt = prompt  # Store the prompt
        url = self.AVAILABLE_MODELS[model]

        payload = {
            "prompt": prompt,
            "model": model if model == "flux-dev" else "stable-diffusion", # Pass model name to API if needed
            "negativePrompt": "", #Use negative prompt from API's data structure
            "cfg": 7,
            "aspectRatio": "1:1",
            "outputFormat": self.image_extension,
            "numOutputs": amount,
            "outputQuality": 90
        }


        image_urls = []
        try:
            with requests.post(url, headers=self.headers, json=payload, timeout=self.timeout) as response:
                if response.status_code != 200:
                    raise exceptions.FailedToGenerateResponseError(f"Request failed with status code: {response.status_code}, {response.text}")  # Raise Webscout exception

                data = response.json()

                if 'output' not in data:
                    raise exceptions.InvalidResponseError("Invalid API response format: 'output' key missing.")

                for img_url in data['output']:
                    image_urls.append(img_url)

        except requests.exceptions.RequestException as e:
            raise exceptions.APIConnectionError(f"An error occurred during the request: {e}") # More specific exception
        except json.JSONDecodeError as e:
            raise exceptions.InvalidResponseError(f"Failed to parse JSON response: {e}")

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

            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToSaveImageError(f"An error occurred while downloading/saving image: {e}")

        return filenames



if __name__ == "__main__":
    bot = NinjaImager()
    try:
        resp = bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
        print(bot.save(resp))
    except Exception as e:
        print(f"An error occurred: {e}")