"""PollinationsAI Provider Package - Your go-to for text-to-image generation! 🎨

Examples:
    >>> # Synchronous usage
    >>> from webscout import PollinationsAI
    >>> provider = PollinationsAI()
    >>> images = provider.generate("A cool cyberpunk city")
    >>> provider.save(images, dir="my_images")
    >>> 
    >>> # Asynchronous usage
    >>> import asyncio
    >>> from webscout import AsyncPollinationsAI
    >>> async def main():
    ...     provider = AsyncPollinationsAI()
    ...     images = await provider.generate("A cool cyberpunk city")
    ...     await provider.save(images, dir="my_images")
    >>> asyncio.run(main())
"""

from .sync_pollinations import PollinationsAI
from .async_pollinations import AsyncPollinationsAI

__all__ = ["PollinationsAI", "AsyncPollinationsAI"]
