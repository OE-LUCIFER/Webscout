import cloudscraper
import os
import requests

from typing import List

from webscout.AIbase import ImageProvider

class ArtbitImager(ImageProvider):
    """
    Image provider for Artbit.ai.
    """

    def __init__(self, timeout: int = 60, proxies: dict = {}):
        """Initializes the ArtbitImager class.

        Args:
            timeout (int, optional): HTTP request timeout in seconds. Defaults to 60.
            proxies (dict, optional): HTTP request proxies. Defaults to {}.
        """
        self.url = "https://artbit.ai/api/generateImage"
        self.scraper = cloudscraper.create_scraper()
        self.scraper.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"

    def generate(
        self, 
        prompt: str, 
        amount: int = 1,
        caption_model: str = "sdxl",
        selected_ratio: str = "1024",
        negative_prompt: str = ""
    ) -> List[str]:
        """Generate image from prompt

        Args:
            prompt (str): Image description.
            amount (int, optional): Total images to be generated. Defaults to 1.
            caption_model (str, optional): Caption model to use. Defaults to "sdxl".
            selected_ratio (str, optional): Image ratio. Defaults to "1024".
            negative_prompt (str, optional): Negative prompt. Defaults to "".

        Returns:
            List[str]: List of generated image URLs.
        """
        assert bool(prompt), "Prompt cannot be null"
        assert isinstance(amount, int), f"Amount should be an integer only not {type(amount)}"
        assert amount > 0, "Amount should be greater than 0"

        self.prompt = prompt
        response: List[str] = []

        payload = {
            "captionInput": prompt,
            "captionModel": caption_model,
            "selectedRatio": selected_ratio,
            "selectedSamples": str(amount),
            "negative_prompt": negative_prompt
        }

        try:
            # Sending the POST request using CloudScraper
            resp = self.scraper.post(self.url, json=payload, timeout=self.timeout)
            resp.raise_for_status()  # Check for HTTP errors

            # Parsing the JSON response
            response_data = resp.json()

            # Extracting image URLs from the response
            imgs = response_data.get("imgs", [])
            if imgs:
                response.extend(imgs)
            else:
                print("No images found in the response.")

        except requests.RequestException as e:
            print(f"An error occurred while making the request: {e}")
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

if __name__ == "__main__":
    bot = ArtbitImager()
    try:
        resp = bot.generate(
            "A shiny red sports car speeding down a scenic mountain road with a clear blue sky in the background, surrounded by lush green trees.",
            amount=3
        )
        print(bot.save(resp))
    except Exception as e:
        print(f"An error occurred: {e}")