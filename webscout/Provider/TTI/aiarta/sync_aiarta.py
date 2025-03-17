"""AIArtaImager Synchronous Provider - Generate stunning AI art with AI Arta! 🎨

Examples:
    >>> from webscout import AIArtaImager
    >>> provider = AIArtaImager()
    >>> 
    >>> # Generate a single image
    >>> images = provider.generate("A cool cyberpunk city at night")
    >>> paths = provider.save(images, dir="my_images")
    >>> 
    >>> # Generate multiple images with different settings
    >>> images = provider.generate(
    ...     prompt="Epic dragon breathing fire",
    ...     amount=2, 
    ...     model="flux"
    ... )
    >>> provider.save(images, dir="dragon_pics")
"""

import requests
import json
import os
import time
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from requests.exceptions import RequestException

from webscout.AIbase import ImageProvider
from webscout.litagent import LitAgent

agent = LitAgent()

class AIArtaImager(ImageProvider):
    """Your go-to provider for generating fire images with AI Arta! 🎨

    Examples:
        >>> provider = AIArtaImager()
        >>> # Generate one image
        >>> image = provider.generate("A futuristic city")
        >>> provider.save(image, "city.png")
        >>> 
        >>> # Generate multiple images with specific model
        >>> images = provider.generate(
        ...     prompt="Space station",
        ...     amount=3,
        ...     model="flux_black_ink"
        ... )
        >>> provider.save(images, dir="space_pics")
    """

    # API endpoints
    url = "https://img-gen-prod.ai-arta.com"
    auth_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key=AIzaSyB3-71wG0fIt0shj0ee4fvx1shcjJHGrrQ"
    token_refresh_url = "https://securetoken.googleapis.com/v1/token?key=AIzaSyB3-71wG0fIt0shj0ee4fvx1shcjJHGrrQ"
    image_generation_url = "https://img-gen-prod.ai-arta.com/api/v1/text2image"
    status_check_url = "https://img-gen-prod.ai-arta.com/api/v1/text2image/{record_id}/status"

    # Available models
    AVAILABLE_MODELS = {
        "flux": "Flux",
        "medieval": "Medieval",
        "vincent_van_gogh": "Vincent Van Gogh",
        "f_dev": "F Dev",
        "low_poly": "Low Poly",
        "dreamshaper_xl": "Dreamshaper-xl",
        "anima_pencil_xl": "Anima-pencil-xl",
        "biomech": "Biomech",
        "trash_polka": "Trash Polka",
        "no_style": "No Style",
        "cheyenne_xl": "Cheyenne-xl",
        "chicano": "Chicano",
        "embroidery_tattoo": "Embroidery tattoo",
        "red_and_black": "Red and Black",
        "fantasy_art": "Fantasy Art",
        "watercolor": "Watercolor",
        "dotwork": "Dotwork",
        "old_school_colored": "Old school colored",
        "realistic_tattoo": "Realistic tattoo",
        "japanese_2": "Japanese_2",
        "realistic_stock_xl": "Realistic-stock-xl",
        "f_pro": "F Pro",
        "revanimated": "RevAnimated",
        "katayama_mix_xl": "Katayama-mix-xl",
        "sdxl_l": "SDXL L",
        "cor_epica_xl": "Cor-epica-xl",
        "anime_tattoo": "Anime tattoo",
        "new_school": "New School",
        "death_metal": "Death metal",
        "old_school": "Old School",
        "juggernaut_xl": "Juggernaut-xl",
        "photographic": "Photographic",
        "sdxl_1_0": "SDXL 1.0",
        "graffiti": "Graffiti",
        "mini_tattoo": "Mini tattoo",
        "surrealism": "Surrealism",
        "neo_traditional": "Neo-traditional",
        "on_limbs_black": "On limbs black",
        # "yamers_realistic_xl": "Yamers-realistic-xl",
        # "pony_xl": "Pony-xl",
        # "playground_xl": "Playground-xl",
        # "anything_xl": "Anything-xl",
        # "flame_design": "Flame design",
        # "kawaii": "Kawaii",
        # "cinematic_art": "Cinematic Art",
        # "professional": "Professional",
        # "flux_black_ink": "Flux Black Ink"
    }
    models = list(AVAILABLE_MODELS.keys())

    def __init__(self, timeout: int = 60, proxies: dict = None, logging: bool = True):
        """Initialize your AIArtaImager provider with custom settings

        Examples:
            >>> provider = AIArtaImager(timeout=120)
            >>> provider = AIArtaImager(proxies={"http": "http://proxy:8080"})

        Args:
            timeout (int): HTTP request timeout in seconds (default: 60)
            proxies (dict, optional): Proxy configuration for requests
            logging (bool): Enable/disable logging (default: True)
        """
        self.headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "User-Agent": agent.random()
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.timeout = timeout
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"


    def get_auth_file(self) -> Path:
        """Get path to authentication file"""
        path = Path(os.path.join(os.path.expanduser("~"), ".ai_arta_cookies"))
        path.mkdir(exist_ok=True)
        filename = f"auth_{self.__class__.__name__}.json"
        return path / filename

    def create_token(self, path: Path) -> Dict[str, Any]:
        """Create a new authentication token"""
        # Step 1: Generate Authentication Token
        auth_payload = {"clientType": "CLIENT_TYPE_ANDROID"}
        proxies = self.session.proxies if self.session.proxies else None
        
        auth_response = self.session.post(self.auth_url, json=auth_payload, timeout=self.timeout, proxies=proxies)
        auth_data = auth_response.json()
        auth_token = auth_data.get("idToken")
        
        if not auth_token:

            raise Exception("Failed to obtain authentication token.")
        
        with open(path, 'w') as f:
            json.dump(auth_data, f)
        
        return auth_data

    def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """Refresh authentication token"""
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        response = self.session.post(self.token_refresh_url, data=payload, timeout=self.timeout)
        response_data = response.json()
        
        return response_data.get("id_token"), response_data.get("refresh_token")

    def read_and_refresh_token(self) -> Dict[str, Any]:
        """Read token from file and refresh if needed"""
        path = self.get_auth_file()
        
        if path.is_file():
            with open(path, 'r') as f:
                auth_data = json.load(f)
            
            diff = time.time() - os.path.getmtime(path)
            expires_in = int(auth_data.get("expiresIn"))
            
            if diff < expires_in:
                if diff > expires_in / 2:
                    auth_data["idToken"], auth_data["refreshToken"] = self.refresh_token(
                        auth_data.get("refreshToken")
                    )
                    with open(path, 'w') as f:
                        json.dump(auth_data, f)
                return auth_data
        
        # Create new token if file doesn't exist or token expired
        return self.create_token(path)

    def get_model(self, model_name: str) -> str:
        """Get actual model name from alias"""
        if model_name.lower() in self.AVAILABLE_MODELS:
            return self.AVAILABLE_MODELS[model_name.lower()]
        return model_name

    def generate(
        self,
        prompt: str,
        amount: int = 1,
        model: str = "Flux",
        negative_prompt: str = "blurry, deformed hands, ugly",
        guidance_scale: int = 7,
        num_inference_steps: int = 30,
        aspect_ratio: str = "1:1",
        max_retries: int = 3,
        retry_delay: int = 5,
        **kwargs
    ) -> List[bytes]:
        """Generate some fire images from your prompt! 🎨

        Examples:
            >>> provider = AIArtaImager()
            >>> # Basic usage
            >>> images = provider.generate("Cool art")
            >>> # Advanced usage
            >>> images = provider.generate(
            ...     prompt="Epic dragon",
            ...     amount=2,
            ...     model="fantasy_art",
            ...     negative_prompt="ugly, deformed"
            ... )

        Args:
            prompt (str): Your image description
            amount (int): How many images you want (default: 1)
            model (str): Model to use - check AVAILABLE_MODELS (default: "flux")
            negative_prompt (str): What you don't want in the image
            guidance_scale (int): Controls how closely the model follows your prompt
            num_inference_steps (int): More steps = better quality but slower
            aspect_ratio (str): Image aspect ratio (default: "1:1")
            max_retries (int): Max retry attempts if something fails
            retry_delay (int): Seconds to wait between retries
            **kwargs: Additional parameters for future compatibility

        Returns:
            List[bytes]: Your generated images

        Raises:
            ValueError: If the inputs ain't valid
            RequestException: If the API calls fail after retries
        """
        if not prompt:
            raise ValueError("Yo fam, the prompt can't be empty! 🤔")
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Amount needs to be a positive number! 📈")
        
        model_name = self.get_model(model)
        self.prompt = prompt
        response = []

        # Step 1: Get Authentication Token
        auth_data = self.read_and_refresh_token()
        
        # Headers for generation requests
        gen_headers = {
            "Authorization": auth_data.get("idToken"),
        }

        for i in range(amount):
            # Step 2: Generate Image
            image_payload = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "style": model_name,
                "images_num": "1",  # Generate 1 at a time
                "cfg_scale": str(guidance_scale),
                "steps": str(num_inference_steps),
                "aspect_ratio": aspect_ratio,
            }

            for attempt in range(max_retries):
                try:
                    
                    # Submit generation request
                    image_response = self.session.post(
                        self.image_generation_url, 
                        data=image_payload, 
                        headers=gen_headers, 
                        timeout=self.timeout
                    )
                    image_response.raise_for_status()
                    image_data = image_response.json()
                    record_id = image_data.get("record_id")

                    if not record_id:
                        raise RequestException(f"Failed to initiate image generation: {image_data}")

                    # Step 3: Check Generation Status
                    status_url = self.status_check_url.format(record_id=record_id)
                    
                    counter = 0
                    dots = [".", "..", "...", "...."]
                    
                    while True:
                        status_response = self.session.get(
                            status_url, 
                            headers=gen_headers, 
                            timeout=self.timeout
                        )
                        status_data = status_response.json()
                        status = status_data.get("status")

                        if status == "DONE":
                            image_urls = [image["url"] for image in status_data.get("response", [])]
                            
                            if not image_urls:
                                raise RequestException("No image URLs in response")
                            
                            # Download the generated image
                            image_response = self.session.get(image_urls[0], timeout=self.timeout)
                            image_response.raise_for_status()
                            response.append(image_response.content)
                            break
                            
                        elif status in ("IN_QUEUE", "IN_PROGRESS"):
                            # status_text = "Waiting" if status == "IN_QUEUE" else "Generating"
                            time.sleep(3) 
                            counter += 1
                            
                        else:
                            raise RequestException(f"Image generation failed with status: {status}")
                    
                    # If we got here, we successfully generated an image
                    break
                    
                except RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    else:
                        time.sleep(retry_delay)

        return response

    def save(
        self,
        response: List[bytes],
        name: Optional[str] = None,
        dir: Optional[Union[str, Path]] = None,
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire generated images! 💾

        Examples:
            >>> provider = AIArtaImager()
            >>> images = provider.generate("Cool art")
            >>> # Save with default settings
            >>> paths = provider.save(images)
            >>> # Save with custom name and directory
            >>> paths = provider.save(
            ...     images,
            ...     name="my_art",
            ...     dir="my_images",
            ...     filenames_prefix="test_"
            ... )

        Args:
            response (List[bytes]): Your generated images
            name (Optional[str]): Custom name for your images
            dir (Optional[Union[str, Path]]): Where to save the images (default: current directory)
            filenames_prefix (str): Prefix for your image files

        Returns:
            List[str]: Paths to your saved images
        """
        save_dir = dir if dir else os.getcwd()
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        name = self.prompt if name is None else name
            
        # Clean up name for filename use
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
        safe_name = safe_name[:50]  # Truncate if too long
            
        filenames = []
        count = 0

        for image in response:
            def complete_path():
                count_value = "" if count == 0 else f"_{count}"
                return os.path.join(save_dir, filenames_prefix + safe_name + count_value + "." + self.image_extension)

            while os.path.isfile(complete_path()):
                count += 1

            filepath = complete_path()
            filenames.append(os.path.basename(filepath))

            with open(filepath, "wb") as fh:
                fh.write(image)
        return filenames


if __name__ == "__main__":
    # Example usage
    bot = AIArtaImager()
    test_prompt = "A shiny red sports car speeding down a scenic mountain road"
    
    print(f"Testing all available models with prompt: '{test_prompt}'")
    print("-" * 50)
    
    # Create a directory for test images if it doesn't exist
    test_dir = "model_test_images"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        
    for model in bot.AVAILABLE_MODELS:
        print(f"Testing model: {model}")
        try:
            # Generate an image with the current model
            resp = bot.generate(
                prompt=test_prompt,
                amount=1,
                model=model,
                width=768,
                height=768
            )
            
            # Save the image with model name as prefix
            saved_paths = bot.save(
                resp, 
                name=f"{model}_test", 
                dir=test_dir, 
                filenames_prefix=f"{model}_"
            )
            
            print(f"✓ Success! Saved image: {saved_paths[0]}")
        except Exception as e:
            print(f"✗ Failed with model {model}: {str(e)}")
        
        print("-" * 30)
    
    print("All model tests completed!")
