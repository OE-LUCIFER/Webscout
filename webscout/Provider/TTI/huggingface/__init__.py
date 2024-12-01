"""
HuggingFace Providers - Your go-to solution for generating fire images! 🔥

Examples:
    >>> # Sync Usage
    >>> from webscout import HFimager
    >>> provider = HFimager(api_token="your-hf-token")
    >>> images = provider.generate("Cool art")
    >>> paths = provider.save(images)
    >>>
    >>> # Async Usage
    >>> from webscout import AsyncHFimager
    >>> async def example():
    ...     provider = AsyncHFimager(api_token="your-hf-token")
    ...     images = await provider.generate("Epic dragon")
    ...     paths = await provider.save(images)
"""

from .sync_huggingface import HFimager
from .async_huggingface import AsyncHFimager

__all__ = ["HFimager", "AsyncHFimager"]
