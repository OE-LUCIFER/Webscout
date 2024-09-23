import os
import requests
import io
from PIL import Image
from typing import Any, List, Optional, Dict
from webscout.AIbase import ImageProvider

class HFimager(ImageProvider):
    """
    Image provider for Hugging Face Inference API.
    """

    def __init__(
        self,
        api_token: str = None,
        timeout: int = 60,
        proxies: dict = {}
    ):
        """Initializes the HFimager class.

        Args:
            api_token (str, optional): Hugging Face API token. If None, it will use the environment variable "HUGGINGFACE_API_TOKEN".
                                       Defaults to None.
            timeout (int, optional): HTTP request timeout in seconds. Defaults to 60.
            proxies (dict, optional): HTTP request proxies. Defaults to {}.
        """
        self.base_url = "https://api-inference.huggingface.co/models/"
        self.api_token = api_token or os.environ["HUGGINGFACE_API_TOKEN"]
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
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
        model: str = "black-forest-labs/FLUX.1-dev",
        guidance_scale: Optional[float] = None,
        negative_prompt: Optional[str] = None,
        num_inference_steps: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        scheduler: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> List[bytes]:
        """
        Generate image from prompt.

        Args:
            prompt (str): Image description.
            amount (int): Total images to be generated. Defaults to 1.
            model (str): Hugging Face model name. Defaults to "black-forest-labs/FLUX.1-dev".
            guidance_scale (float, optional): Guidance scale value. Defaults to None.
            negative_prompt (str, optional): Negative prompt. Defaults to None.
            num_inference_steps (int, optional): Number of inference steps. Defaults to None.
            width (int, optional): Width of the output image. Defaults to None.
            height (int, optional): Height of the output image. Defaults to None.
            scheduler (str, optional): Scheduler to use. Defaults to None.
            seed (int, optional): Seed for random number generator. Defaults to None.

        Returns:
            List[bytes]: List of generated images as bytes.
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"

        self.prompt = prompt
        response = []

        for _ in range(amount):
            url = self.base_url + model

            # Create the base payload with the prompt
            payload: Dict[str, Any] = {"inputs": prompt}

            # Add optional parameters to the payload if provided
            parameters = {}
            if guidance_scale is not None:
                parameters["guidance_scale"] = guidance_scale
            if negative_prompt is not None:
                parameters["negative_prompt"] = negative_prompt
            if num_inference_steps is not None:
                parameters["num_inference_steps"] = num_inference_steps
            if width is not None and height is not None:
                parameters["target_size"] = {"width": width, "height": height}
            if scheduler is not None:
                parameters["scheduler"] = scheduler
            if seed is not None:
                parameters["seed"] = seed

            # Add the parameters to the payload if any are set
            if parameters:
                payload["parameters"] = parameters

            try:
                resp = self.session.post(url, headers=self.headers, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                response.append(resp.content)
            except requests.RequestException as e:
                print(f"Failed to generate image: {e}")
                raise

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
        for image_bytes in response:
            def complete_path():
                count_value = "" if count == 0 else f"_{count}"
                return os.path.join(dir, name + count_value + "." + self.image_extension)

            while os.path.isfile(complete_path()):
                count += 1

            absolute_path_to_file = complete_path()
            filenames.append(filenames_prefix + os.path.split(absolute_path_to_file)[1])

            with open(absolute_path_to_file, "wb") as fh:
                fh.write(image_bytes)

        return filenames

if __name__ == "__main__":
    bot = HFimager(api_token='your huggingface API')
    try:
        resp = bot.generate("A shiny red sports car speeding down a scenic mountain road with a clear blue sky in the background, surrounded by lush green trees.", 1)
        print(bot.save(resp, name="test"))
    except Exception as e:
        print(f"An error occurred: {e}")