"""
AiForce - Your go-to provider for generating fire images! 🔥

Examples:
    >>> # Sync Usage
    >>> from webscout import AiForceimager
    >>> provider = AiForceimager()
    >>> images = provider.generate("Cool art")
    >>> paths = provider.save(images)
    >>>
    >>> # Async Usage
    >>> from webscout import AsyncAiForceimager
    >>> async def example():
    ...     provider = AsyncAiForceimager()
    ...     images = await provider.generate("Epic dragon")
    ...     paths = await provider.save(images)
"""

from .sync_aiforce import AiForceimager
from .async_aiforce import AsyncAiForceimager

__all__ = ["AiForceimager", "AsyncAiForceimager"]
