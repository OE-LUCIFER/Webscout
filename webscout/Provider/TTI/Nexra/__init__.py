"""
Nexra - Your go-to provider for generating fire images! 🔥

Examples:
    >>> # Sync Usage
    >>> from webscout import NexraImager
    >>> provider = NexraImager()
    >>> images = provider.generate("Cool art")
    >>> paths = provider.save(images)
    >>>
    >>> # Async Usage
    >>> from webscout import AsyncNexraImager
    >>> async def example():
    ...     provider = AsyncNexraImager()
    ...     images = await provider.generate("Epic dragon")
    ...     paths = await provider.save(images)
"""

from .sync_nexra import NexraImager
from .async_nexra import AsyncNexraImager

__all__ = ["NexraImager", "AsyncNexraImager"]
