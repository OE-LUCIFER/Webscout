import requests
import os
from typing import List

from webscout.AIbase import ImageProvider

class WebSimAI(ImageProvider):
    """
    Image provider for WebSim.ai.
    """

    def __init__(self, timeout: int = 60, proxies: dict = {}):
        """Initializes the WebSimAI class.

        Args:
            timeout (int, optional): HTTP request timeout in seconds. Defaults to 60.
            proxies (dict, optional): HTTP request proxies (socks). Defaults to {}.
        """
        self.url = "https://websim.ai/api/image_gen"
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
            ),
            "Origin": "https://websim.ai",
            "Referer": "https://websim.ai/p/a5yvwmtj8qz6ayx4tlg1"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - Webscout"
        self.image_extension: str = "png"  

    def generate(
        self, 
        prompt: str, 
        amount: int = 1, 
        width: int = 1024, 
        height: int = 756
    ) -> List[bytes]:
        """Generate image from prompt

        Args:
            prompt (str): Image description.
            amount (int, optional): Total images to be generated. Defaults to 1.
            width (int, optional): Width of the generated image. Defaults to 1024.
            height (int, optional): Height of the generated image. Defaults to 756.

        Returns:
            List[bytes]: List of generated images as bytes.
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only, not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"

        self.prompt = prompt
        response = []

        for _ in range(amount):
            payload = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "site_id": "KcWvHOHNBP2PmWUYZ",
            }

            try:
                resp = self.session.post(self.url, headers=self.headers, json=payload, timeout=self.timeout)
                resp.raise_for_status()  # Raises HTTPError for bad responses

                response_data = resp.json()
                image_url = response_data.get("url")
                if not image_url:
                    print("No image URL found in the response.")
                    continue

                image_response = requests.get(image_url)
                image_response.raise_for_status()
                response.append(image_response.content)

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err} - {response.text}")
                return []  # Return an empty list on error
            except requests.exceptions.RequestException as req_err:
                print(f"Request error occurred: {req_err}")
                return []  # Return an empty list on error

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
    bot = WebSimAI()
    try:
        resp = bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
        print(bot.save(resp))
    except Exception as e:
        print(f"An error occurred: {e}")