import requests
import os
from typing import List
from string import punctuation
from random import choice
from random import randint
import base64

from webscout.AIbase import ImageProvider

class DeepInfraImager(ImageProvider):
    """DeepInfra Image provider"""

    def __init__(
        self,
        model: str = "black-forest-labs/FLUX-1-schnell",
        timeout: int = 60,
        proxies: dict = {},
    ):
        """Initializes `DeepInfraImager`

        Args:
            model (str, optional): The name of the DeepInfra model to use. 
                                        Defaults to "black-forest-labs/FLUX-1-schnell".
            timeout (int, optional): Http request timeout. Defaults to 60 seconds.
            proxies (dict, optional): Http request proxies (socks). Defaults to {}.
        """
        self.image_gen_endpoint: str = f"https://api.deepinfra.com/v1/inference/{model}"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
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

    def generate(
        self, prompt: str, amount: int = 1, additives: bool = True, 
        num_inference_steps: int = 25, guidance_scale: float = 7.5, 
        width: int = 1024, height: int = 1024, seed: int = None
    ) -> list[bytes]:
        """Generate image from prompt

        Args:
            prompt (str): Image description.
            amount (int): Total images to be generated. Defaults to 1.
            additives (bool, optional): Try to make each prompt unique. Defaults to True.
            num_inference_steps (int, optional): Number of inference steps. Defaults to 39.
            guidance_scale (float, optional): Guidance scale for image generation. Defaults to 13.3.
            width (int, optional): Width of the generated image. Defaults to 1024.
            height (int, optional): Height of the generated image. Defaults to 1024.
            seed (int, optional): Random seed for image generation. If None, a random seed is used. 
                                  Defaults to None.

        Returns:
            list[bytes]: List of generated images as bytes.
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
            resp = self.session.post(url=self.image_gen_endpoint, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            # Extract base64 encoded image data and decode it
            image_data = resp.json()['images'][0].split(",")[1]
            image_bytes = base64.b64decode(image_data)
            response.append(image_bytes)

        return response

    def save(
        self,
        response: list[bytes],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> list[str]:
        """Save generated images

        Args:
            response (list[bytes]): List of generated images as bytes.
            name (str):  Filename for the images. Defaults to last prompt.
            dir (str, optional): Directory for saving images. Defaults to os.getcwd().
            filenames_prefix (str, optional): String to be prefixed at each filename to be returned.
        """
        assert isinstance(response, list), f"Response should be of {list} not {type(response)}"
        name = self.prompt if name is None else name

        filenames: list = []
        count = 0
        for image in response:
            def complete_path():
                count_value = "" if count == 0 else f"_{count}"
                return os.path.join(
                    dir, name + count_value + "." + self.image_extension
                )

            while os.path.isfile(complete_path()):
                count += 1

            absolute_path_to_file = complete_path()
            filenames.append(filenames_prefix + os.path.split(absolute_path_to_file)[1])

            with open(absolute_path_to_file, "wb") as fh:
                fh.write(image)

        return filenames


if __name__ == "__main__":
    bot = DeepInfraImager()
    resp = bot.generate("AI-generated image - webscout", 1)
    print(bot.save(resp))