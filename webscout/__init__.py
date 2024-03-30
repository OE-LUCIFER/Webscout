"""Webscout.

Search for words, documents, images, videos, news, maps and text translation 
using the DuckDuckGo.com search engine.
"""

import logging
from .webscout_search import WEBS
from .webscout_search_async import AsyncWEBS
from .version import __version__
from .DWEBS import DeepWEBS
__all__ = ["WEBS", "AsyncWEBS", "__version__", "cli"]

logging.getLogger("webscout").addHandler(logging.NullHandler())
