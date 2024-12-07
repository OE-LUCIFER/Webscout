"""
Scout: A powerful, zero-dependency web scraping library
"""

from .core import Scout
from .element import Tag, NavigableString

__all__ = ['Scout', 'Tag', 'NavigableString']

# Alias for BeautifulSoup compatibility
BeautifulSoup = Scout
