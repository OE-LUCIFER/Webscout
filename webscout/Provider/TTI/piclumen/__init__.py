"""PiclumenImager Provider Package - Your go-to for high-quality AI art! 🎨

Examples:
    >>> # Synchronous usage
    >>> from webscout import PiclumenImager
    >>> provider = PiclumenImager()
    >>> images = provider.generate("A cool underwater creature")
    >>> provider.save(images, dir="my_images")
    >>> 
    >>> # Asynchronous usage
    >>> import asyncio
    >>> from webscout import AsyncPiclumenImager
    >>> async def main():
    ...     provider = AsyncPiclumenImager()
    ...     images = await provider.generate("A cool cyberpunk city")
    ...     await provider.save(images, dir="my_images")
    >>> asyncio.run(main())
"""

from .sync_piclumen import PiclumenImager
from .async_piclumen import AsyncPiclumenImager

__all__ = ["PiclumenImager", "AsyncPiclumenImager"]