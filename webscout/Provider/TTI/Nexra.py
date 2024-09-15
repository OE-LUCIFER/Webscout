import requests
import json
import os
import time
from typing import List, Optional
from requests.exceptions import RequestException

from webscout.AIbase import ImageProvider

class NexraImager(ImageProvider):
    """Image provider for Nexra API"""

    AVAILABLE_MODELS = {
        "standard": ["emi", "stablediffusion-1.5", "stablediffusion-2.1", "sdxl-lora", "dalle", "dalle2", "dalle-mini"],
        "prodia": [
            "dreamshaperXL10_alpha2.safetensors [c8afe2ef]",
            "dynavisionXL_0411.safetensors [c39cc051]",
            "juggernautXL_v45.safetensors [e75f5471]",
            "realismEngineSDXL_v10.safetensors [af771c3f]",
            "sd_xl_base_1.0.safetensors [be9edd61]",
            "animagineXLV3_v30.safetensors [75f2f05b]",
            "sd_xl_base_1.0_inpainting_0.1.safetensors [5679a81a]",
            "turbovisionXL_v431.safetensors [78890989]",
            "devlishphotorealism_sdxl15.safetensors [77cba69f]",
            "realvisxlV40.safetensors [f7fdcb51]"
        ]
    }

    def __init__(self, timeout: int = 60, proxies: dict = {}):
        self.url = "https://nexra.aryahcr.cc/api/image/complements"
        self.headers = {"Content-Type": "application/json"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"

    def generate(
        self, prompt: str, model: str = "emi", amount: int = 1,
        max_retries: int = 3, retry_delay: int = 5,
        additional_params: Optional[dict] = None
    ) -> List[bytes]:
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int) and amount > 0, "Amount should be a positive integer"

        self.prompt = prompt
        response = []

        payload = {
            "prompt": prompt,
            "model": "prodia" if model in self.AVAILABLE_MODELS["prodia"] else model,
        }

        if model in self.AVAILABLE_MODELS["prodia"]:
            payload["data"] = {
                "model": model,
                "steps": 25,
                "cfg_scale": 7,
                "sampler": "DPM++ 2M Karras",
                "negative_prompt": ""
            }
        if additional_params:
            payload.update(additional_params)

        for _ in range(max_retries):
            try:
                resp = self.session.post(self.url, json=payload, timeout=self.timeout)
                resp.raise_for_status()

                # Remove leading underscores and then parse JSON
                response_data = json.loads(resp.text.lstrip("_"))

                if response_data.get("status") and "images" in response_data:
                    for image_url in response_data["images"]:
                        img_resp = requests.get(image_url)
                        img_resp.raise_for_status()
                        response.append(img_resp.content)
                    break
                else:
                    raise Exception("Failed to generate image: " + str(response_data))
            except json.JSONDecodeError as json_err:
                print(f"JSON Decode Error: {json_err}")
                print(f"Raw response: {resp.text}")
                if _ == max_retries - 1:
                    raise
            except RequestException as e:
                print(f"Request Exception: {e}")
                if _ == max_retries - 1:
                    raise
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

        return response

    def save(
        self,
        response: List[bytes],
        name: str = None,
        dir: str = os.getcwd(),
        filenames_prefix: str = "",
    ) -> List[str]:
        assert isinstance(response, list), f"Response should be a list, not {type(response)}"
        name = self.prompt if name is None else name

        filenames = []
        for i, image in enumerate(response):
            filename = f"{filenames_prefix}{name}_{i}.{self.image_extension}"
            filepath = os.path.join(dir, filename)

            with open(filepath, "wb") as fh:
                fh.write(image)
            filenames.append(filename)

        return filenames

if __name__ == "__main__":
    bot = NexraImager()
    resp_standard = bot.generate("AI-generated image - webscout", "emi", 1)
    print(bot.save(resp_standard))
