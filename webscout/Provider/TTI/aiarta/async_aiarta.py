"""
AsyncAIArtaImager - Your go-to async provider for generating fire images with AI Arta! ⚡

Examples:
    >>> from webscout import AsyncAIArtaImager
    >>> import asyncio
    >>> 
    >>> async def example():
    ...     # Initialize with logging
    ...     provider = AsyncAIArtaImager(logging=True)
    ...     
    ...     # Generate a single image
    ...     images = await provider.generate("A beautiful sunset over mountains")
    ...     paths = await provider.save(images)
    ...     
    ...     # Generate multiple images with parameters
    ...     images = await provider.generate(
    ...         prompt="Epic dragon in cyberpunk city",
    ...         amount=2,
    ...         model="fantasy_art",
    ...         negative_prompt="ugly, deformed",
    ...         guidance_scale=7,
    ...         num_inference_steps=30
    ...     )
    ...     paths = await provider.save(images, name="dragon", dir="outputs")
    >>> 
    >>> # Run the example
    >>> asyncio.run(example())
"""

import aiohttp
import asyncio
import json
import os
import time
from pathlib import Path
from typing import List, Optional, Union, Dict, Any, AsyncGenerator
import aiofiles

from webscout.AIbase import AsyncImageProvider
from webscout.litagent import LitAgent

class AsyncAIArtaImager(AsyncImageProvider):
    """Your go-to async provider for generating fire images with AI Arta! ⚡

    Examples:
        >>> provider = AsyncAIArtaImager()
        >>> async def example():
        ...     # Basic usage
        ...     images = await provider.generate("Cool art")
        ...     paths = await provider.save(images)
        >>>
        >>> # Advanced usage
        >>> provider = AsyncAIArtaImager(timeout=120)
        >>> async def example():
        ...     images = await provider.generate(
        ...         prompt="Epic dragon",
        ...         amount=2,
        ...         model="fantasy_art",
        ...         negative_prompt="ugly, deformed"
        ...     )
        ...     paths = await provider.save(images, name="dragon", dir="my_art")
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
        """Initialize your async AIArtaImager provider with custom settings ⚙️

        Args:
            timeout (int): HTTP request timeout in seconds (default: 60)
            proxies (dict, optional): Proxy configuration for requests
            logging (bool): Enable/disable logging (default: True)
        """
        self.headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "User-Agent": LitAgent().random()
        }
        self.timeout = timeout
        self.proxies = proxies
        self.prompt: str = "AI-generated image - webscout"
        self.image_extension: str = "png"
        self.logging = logging
        
        if self.logging and False:  # Disabled logger
            print("AsyncAIArtaImager initialized! Ready to create some fire art! 🚀")

    async def get_auth_file(self) -> Path:
        """Get path to authentication file"""
        path = Path(os.path.join(os.path.expanduser("~"), ".ai_arta_cookies"))
        path.mkdir(exist_ok=True)
        filename = f"auth_{self.__class__.__name__}.json"
        return path / filename

    async def create_token(self, path: Path) -> Dict[str, Any]:
        """Create a new authentication token"""
        # Step 1: Generate Authentication Token
        auth_payload = {"clientType": "CLIENT_TYPE_ANDROID"}
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                self.auth_url, 
                json=auth_payload, 
                timeout=self.timeout,
                proxy=self.proxies.get('http') if self.proxies else None
            ) as response:
                response.raise_for_status()
                auth_data = await response.json()
                
        auth_token = auth_data.get("idToken")
        
        if not auth_token:
            if self.logging:
                print("Failed to obtain authentication token 😢")
            raise Exception("Failed to obtain authentication token.")
        
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(auth_data))
        
        return auth_data

    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """Refresh authentication token"""
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                self.token_refresh_url, 
                data=payload, 
                timeout=self.timeout,
                proxy=self.proxies.get('http') if self.proxies else None
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
        
        return response_data.get("id_token"), response_data.get("refresh_token")

    async def read_and_refresh_token(self) -> Dict[str, Any]:
        """Read token from file and refresh if needed"""
        path = await self.get_auth_file()
        
        if path.is_file():
            async with aiofiles.open(path, 'r') as f:
                auth_data = json.loads(await f.read())
            
            diff = time.time() - os.path.getmtime(path)
            expires_in = int(auth_data.get("expiresIn"))
            
            if diff < expires_in:
                if diff > expires_in / 2:
                    # Refresh token if it's older than half its lifetime
                    if self.logging:
                        print("Refreshing authentication token... 🔄")
                    auth_data["idToken"], auth_data["refreshToken"] = await self.refresh_token(
                        auth_data.get("refreshToken")
                    )
                    async with aiofiles.open(path, 'w') as f:
                        await f.write(json.dumps(auth_data))
                return auth_data
        
        # Create new token if file doesn't exist or token expired
        if self.logging:
            print("Creating new authentication token... 🔑")
        return await self.create_token(path)

    def get_model(self, model_name: str) -> str:
        """Get actual model name from alias"""
        if model_name.lower() in self.AVAILABLE_MODELS:
            return self.AVAILABLE_MODELS[model_name.lower()]
        return model_name

    async def generate(
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
        """Generate some fire images from your prompt asynchronously! ⚡

        Examples:
            >>> provider = AsyncAIArtaImager()
            >>> async def example():
            ...     # Basic usage
            ...     images = await provider.generate("Cool art")
            ...     # Advanced usage
            ...     images = await provider.generate(
            ...         prompt="Epic dragon",
            ...         amount=2,
            ...         model="fantasy_art",
            ...         negative_prompt="ugly, deformed"
            ...     )

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
            Exception: If the API calls fail after retries
        """
        if not prompt:
            raise ValueError("Yo fam, the prompt can't be empty! 🤔")
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Amount needs to be a positive number! 📈")
        
        model_name = self.get_model(model)
        self.prompt = prompt
        response = []

        if self.logging:
            print(f"Generating {amount} images with {model_name}... 🎨")

        # Step 1: Get Authentication Token
        auth_data = await self.read_and_refresh_token()
        
        # Headers for generation requests
        gen_headers = {
            "Authorization": auth_data.get("idToken"),
        }
        
        async with aiohttp.ClientSession(headers={**self.headers, **gen_headers}) as session:
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
                        if self.logging:
                            print(f"Starting generation for image {i+1}/{amount}... ⏳")
                        
                        # Submit generation request
                        async with session.post(
                            self.image_generation_url, 
                            data=image_payload, 
                            timeout=self.timeout,
                            proxy=self.proxies.get('http') if self.proxies else None
                        ) as image_response:
                            image_response.raise_for_status()
                            image_data = await image_response.json()
                        
                        record_id = image_data.get("record_id")

                        if not record_id:
                            if self.logging:
                                print("Failed to initiate image generation 😢")
                            raise Exception(f"Failed to initiate image generation: {image_data}")

                        # Step 3: Check Generation Status
                        status_url = self.status_check_url.format(record_id=record_id)
                        
                        counter = 0
                        dots = [".", "..", "...", "...."]
                        
                        while True:
                            async with session.get(
                                status_url,
                                timeout=self.timeout,
                                proxy=self.proxies.get('http') if self.proxies else None
                            ) as status_response:
                                status_data = await status_response.json()
                            
                            status = status_data.get("status")

                            if status == "DONE":
                                image_urls = [image["url"] for image in status_data.get("response", [])]
                                
                                if not image_urls:
                                    if self.logging:
                                        print("No image URLs in response 😢")
                                    raise Exception("No image URLs in response")
                                
                                # Download the generated image
                                async with session.get(image_urls[0]) as img_response:
                                    img_response.raise_for_status()
                                    response.append(await img_response.read())
                                
                                if self.logging:
                                    print(f"Successfully generated image {i+1}/{amount}! 🎨")
                                break
                                
                            elif status in ("IN_QUEUE", "IN_PROGRESS"):
                                status_text = "Waiting" if status == "IN_QUEUE" else "Generating"
                                if self.logging:
                                    print(f"{status_text}{dots[counter % 4]}")
                                await asyncio.sleep(5)  # Poll every 5 seconds
                                counter += 1
                                
                            else:
                                if self.logging:
                                    print(f"Generation failed with status: {status} 😢")
                                raise Exception(f"Image generation failed with status: {status}")
                        
                        # If we got here, we successfully generated an image
                        break
                        
                    except Exception as e:
                        if attempt == max_retries - 1:
                            if self.logging:
                                print(f"Failed after {max_retries} attempts: {e} 😢")
                            raise
                        else:
                            if self.logging:
                                print(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds... 🔄")
                            await asyncio.sleep(retry_delay)

        if self.logging:
            print(f"Successfully generated {len(response)} images! 🎉")
        return response

    async def save(
        self,
        response: Union[List[bytes], AsyncGenerator[bytes, None]],
        name: Optional[str] = None,
        dir: Optional[Union[str, Path]] = None,
        filenames_prefix: str = "",
    ) -> List[str]:
        """Save your fire generated images asynchronously! 💾

        Examples:
            >>> provider = AsyncAIArtaImager()
            >>> async def example():
            ...     images = await provider.generate("Cool art")
            ...     # Save with default settings
            ...     paths = await provider.save(images)
            ...     # Save with custom name and directory
            ...     paths = await provider.save(
            ...         images,
            ...         name="my_art",
            ...         dir="my_images",
            ...         filenames_prefix="test_"
            ...     )

        Args:
            response (Union[List[bytes], AsyncGenerator[bytes, None]]): Your generated images
            name (Optional[str]): Custom name for your images
            dir (Optional[Union[str, Path]]): Where to save the images (default: current directory)
            filenames_prefix (str): Prefix for your image files

        Returns:
            List[str]: Paths to your saved images
        """
        save_dir = dir if dir else os.getcwd()
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            if self.logging:
                print(f"Created directory: {save_dir} 📁")

        name = self.prompt if name is None else name
        
        # Clean up name for filename use
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
        safe_name = safe_name[:50]  # Truncate if too long
        
        # Handle both List[bytes] and AsyncGenerator
        if isinstance(response, list):
            image_list = response
        else:
            image_list = [chunk async for chunk in response]

        if self.logging:
            print(f"Saving {len(image_list)} images... 💾")
            
        saved_paths = []
        
        async def save_single_image(image_bytes: bytes, index: int) -> str:
            filename = f"{filenames_prefix}{safe_name}_{index}.{self.image_extension}"
            filepath = os.path.join(save_dir, filename)
            
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(image_bytes)
            
            if self.logging:
                print(f"Saved image to: {filepath} 💾")
            return filename

        tasks = [save_single_image(img, i) for i, img in enumerate(image_list)]
        saved_paths = await asyncio.gather(*tasks)

        if self.logging:
            print(f"Images saved successfully! Check {dir} 🎉")
        return saved_paths


if __name__ == "__main__":
    # Example usage
    async def main():
        provider = AsyncAIArtaImager()
        try:
            images = await provider.generate("A beautiful sunset over mountains", amount=1)
            paths = await provider.save(images, dir="generated_images")
            print(f"Images saved to: {paths}")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    asyncio.run(main())