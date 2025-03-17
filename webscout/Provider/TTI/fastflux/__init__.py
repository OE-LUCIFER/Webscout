"""
FastFlux Image Generator - Your go-to provider for generating fire images! 🔥

Examples:
    >>> # Sync Usage
    >>> from webscout import FastFluxImager
    >>> provider = FastFluxImager()
    >>> images = provider.generate("Cool art")
    >>> paths = provider.save(images)
    >>>
    >>> # Async Usage
    >>> from webscout import AsyncFastFluxImager
    >>> async def example():
    ...     provider = AsyncFastFluxImager()
    ...     images = await provider.generate("Epic dragon")
    ...     paths = await provider.save(images)
"""

from .sync_fastflux import FastFluxImager
from .async_fastflux import AsyncFastFluxImager

__all__ = ["FastFluxImager", "AsyncFastFluxImager"]
