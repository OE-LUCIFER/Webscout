"""ImgSys Provider Package - Generate images from multiple providers! 🎨

Examples:
    >>> # Synchronous usage
    >>> from webscout import ImgSys
    >>> provider = ImgSys()
    >>> images = provider.generate("A cool cyberpunk city")
    >>> provider.save(images, dir="my_images")
    >>> 
    >>> # Asynchronous usage
    >>> import asyncio
    >>> from webscout import AsyncImgSys
    >>> async def main():
    ...     provider = AsyncImgSys()
    ...     images = await provider.generate("A cool cyberpunk city")
    ...     await provider.save(images, dir="my_images")
    >>> asyncio.run(main())
"""

from .sync_imgsys import ImgSys
from .async_imgsys import AsyncImgSys

__all__ = ["ImgSys", "AsyncImgSys"] 