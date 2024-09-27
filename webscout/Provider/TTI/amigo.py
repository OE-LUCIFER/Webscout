import requests
import json
import uuid
import os
from typing import List

from webscout.AIbase import ImageProvider

class AmigoImager(ImageProvider):
    """
    Image provider for AmigoChat.io.
    """
    AVAILABLE_MODELS = ["dalle-e-3", "flux-pro", "flux-realism"] 
    def __init__(self, timeout: int = 60, proxies: dict = {}):
        """Initializes the AmigoImager class.

        Args:
            timeout (int, optional): HTTP request timeout in seconds. Defaults to 60.
            proxies (dict, optional): HTTP request proxies. Defaults to {}.
        """
        self.url = "https://api.amigochat.io/v1/images/generations"
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Authorization": "Bearer ",  # Empty
            "Content-Type": "application/json; charset=utf-8",
            "DNT": "1",
            "Origin": "https://amigochat.io",
            "Referer": "https://amigochat.io/",
            "Sec-CH-UA": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            "X-Device-Language": "en-US",
            "X-Device-Platform": "web",
            "X-Device-UUID": str(uuid.uuid4()),
            "X-Device-Version": "1.0.22"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"

    def generate(self, prompt: str, amount: int = 1, model: str = "flux-pro") -> List[str]:
        """Generate image from prompt

        Args:
            prompt (str): Image description.
            amount (int, optional): Total images to be generated. Defaults to 1.
            model (str, optional): Model to use for generating images. Defaults to "flux-pro".

        Returns:
            List[str]: List of generated image URLs.
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"
        assert model in self.AVAILABLE_MODELS, f"Model should be one of {self.AVAILABLE_MODELS}"

        self.prompt = prompt
        response = []

        for _ in range(amount):
            # JSON payload for the request
            payload = {
                "prompt": prompt,
                "model": model,
                "personaId": "image-generator"
            }
            
            try:
                # Sending the POST request
                resp = requests.post(self.url, headers=self.headers, data=json.dumps(payload), timeout=self.timeout)
                resp.raise_for_status()

                # Process the response
                response_data = resp.json()
                image_url = response_data['data'][0]['url']
                response.append(image_url)

            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")
                raise

        return response
    
    def save(
        self,
        response: List[str],  # List of image URLs
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save generated images

        Args:
            response (List[str]): List of generated image URLs.
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
        for img_url in response:
            def complete_path():
                count_value = "" if count == 0 else f"_{count}"
                return os.path.join(dir, name + count_value + "." + self.image_extension)

            while os.path.isfile(complete_path()):
                count += 1

            absolute_path_to_file = complete_path()
            filenames.append(filenames_prefix + os.path.split(absolute_path_to_file)[1])

            # Download and save the image
            try:
                img_response = requests.get(img_url, stream=True, timeout=self.timeout)
                img_response.raise_for_status()

                with open(absolute_path_to_file, "wb") as fh:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        fh.write(chunk)
            except requests.exceptions.RequestException as e:
                print(f"An error occurred while downloading image from {img_url}: {e}")
                raise

        return filenames

# Example usage
if __name__ == "__main__":
    bot = AmigoImager()
    try:
        resp = bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
        print(bot.save(resp))
    except Exception as e:
        print(f"An error occurred: {e}")