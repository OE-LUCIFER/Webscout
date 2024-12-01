"""
Artbit Providers - Your go-to solution for generating fire images! 🔥

Examples:
    >>> # Sync Usage
    >>> from webscout import ArtbitImager
    >>> provider = ArtbitImager(logging=True)
    >>> images = provider.generate("Cool art")
    >>> paths = provider.save(images)
    >>>
    >>> # Async Usage
    >>> from webscout import AsyncArtbitImager
    >>> async def example():
    ...     provider = AsyncArtbitImager(logging=True)
    ...     images = await provider.generate("Epic dragon")
    ...     paths = await provider.save(images)
"""

from .sync_artbit import ArtbitImager
from .async_artbit import AsyncArtbitImager

__all__ = ["ArtbitImager", "AsyncArtbitImager"]
