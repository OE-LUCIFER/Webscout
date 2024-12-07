"""
Scout - The next-gen web scraping library! 🚀
A powerful, flexible, and performant HTML parsing library.
Enhanced with advanced features and intelligent parsing.
"""

import sys
import re
import warnings
import json
import hashlib
import unicodedata
import os
import requests
from markdownify import MarkdownConverter
import concurrent.futures
import urllib.parse
from collections import Counter, defaultdict
from typing import Union, List, Dict, Optional, Callable, Any, Tuple, Iterator, Set

from .parsers.html_parser import HTMLParser
from .parsers.lxml_parser import LXMLParser
from .parsers.html5lib_parser import HTML5Parser
from .element import Tag, NavigableString
from .utils import decode_markup

class ScoutTextAnalyzer:
    """
    Advanced text analysis and processing utility.
    """
    @staticmethod
    def tokenize(text: str, lowercase=True, remove_punctuation=True) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text (str): Input text
            lowercase (bool, optional): Convert to lowercase
            remove_punctuation (bool, optional): Remove punctuation
        
        Returns:
            List[str]: List of tokens
        """
        if lowercase:
            text = text.lower()
        
        if remove_punctuation:
            text = re.sub(r'[^\w\s]', '', text)
        
        return text.split()
    
    @staticmethod
    def count_words(text: str) -> Dict[str, int]:
        """
        Count word frequencies.
        
        Args:
            text (str): Input text
        
        Returns:
            Dict[str, int]: Word frequency dictionary
        """
        return dict(Counter(ScoutTextAnalyzer.tokenize(text)))
    
    @staticmethod
    def extract_entities(text: str) -> Dict[str, Set[str]]:
        """
        Extract named entities from text.
        
        Args:
            text (str): Input text
        
        Returns:
            Dict[str, Set[str]]: Extracted entities
        """
        entities = {
            'emails': set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)),
            'urls': set(re.findall(r'https?://\S+', text)),
            'phones': set(re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)),
            'dates': set(re.findall(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', text))
        }
        return entities

class ScoutWebAnalyzer:
    """
    Advanced web content analysis utility.
    """
    @staticmethod
    def analyze_page_structure(scout_obj: 'Scout') -> Dict[str, Any]:
        """
        Analyze the structure of a web page.
        
        Args:
            scout_obj (Scout): Parsed Scout object
        
        Returns:
            Dict[str, Any]: Page structure analysis
        """
        analysis = {
            'tag_distribution': {},
            'class_distribution': {},
            'id_distribution': {},
            'depth_analysis': {}
        }
        
        # Tag distribution
        for tag in scout_obj.find_all():
            analysis['tag_distribution'][tag.name] = analysis['tag_distribution'].get(tag.name, 0) + 1
        
        # Class distribution
        for tag in scout_obj.find_all(attrs={'class': True}):
            for cls in tag.get('class', []):
                analysis['class_distribution'][cls] = analysis['class_distribution'].get(cls, 0) + 1
        
        # ID distribution
        for tag in scout_obj.find_all(attrs={'id': True}):
            analysis['id_distribution'][tag.get('id')] = analysis['id_distribution'].get(tag.get('id'), 0) + 1
        
        # Depth analysis
        def _analyze_depth(tag, current_depth=0):
            analysis['depth_analysis'][current_depth] = analysis['depth_analysis'].get(current_depth, 0) + 1
            for child in tag.contents:
                if isinstance(child, Tag):
                    _analyze_depth(child, current_depth + 1)
        
        _analyze_depth(scout_obj._soup)
        
        return analysis

class ScoutSearchResult:
    """
    Represents a search result with advanced querying capabilities.
    Enhanced with more intelligent filtering and processing.
    """
    def __init__(self, results: List[Tag]):
        """
        Initialize a search result collection.
        
        Args:
            results (List[Tag]): List of matching tags
        """
        self._results = results
    
    def __len__(self) -> int:
        return len(self._results)
    
    def __iter__(self) -> Iterator[Tag]:
        return iter(self._results)
    
    def __getitem__(self, index: Union[int, slice]) -> Union[Tag, List[Tag]]:
        return self._results[index]
    
    def texts(self, separator=' ', strip=True) -> List[str]:
        """
        Extract texts from all results.
        
        Args:
            separator (str, optional): Text separator
            strip (bool, optional): Strip whitespace
        
        Returns:
            List[str]: List of extracted texts
        """
        return [tag.get_text(separator, strip) for tag in self._results]
    
    def attrs(self, attr_name: str) -> List[Any]:
        """
        Extract a specific attribute from all results.
        
        Args:
            attr_name (str): Attribute name to extract
        
        Returns:
            List[Any]: List of attribute values
        """
        return [tag.get(attr_name) for tag in self._results]
    
    def filter(self, predicate: Callable[[Tag], bool]) -> 'ScoutSearchResult':
        """
        Filter results using a predicate function.
        
        Args:
            predicate (Callable[[Tag], bool]): Filtering function
        
        Returns:
            ScoutSearchResult: Filtered search results
        """
        return ScoutSearchResult([tag for tag in self._results if predicate(tag)])
    
    def map(self, transform: Callable[[Tag], Any]) -> List[Any]:
        """
        Transform results using a mapping function.
        
        Args:
            transform (Callable[[Tag], Any]): Transformation function
        
        Returns:
            List[Any]: Transformed results
        """
        return [transform(tag) for tag in self._results]
    
    def analyze_text(self) -> Dict[str, Any]:
        """
        Perform text analysis on search results.
        
        Returns:
            Dict[str, Any]: Text analysis results
        """
        texts = self.texts(strip=True)
        full_text = ' '.join(texts)
        
        return {
            'total_results': len(self._results),
            'word_count': ScoutTextAnalyzer.count_words(full_text),
            'entities': ScoutTextAnalyzer.extract_entities(full_text)
        }

class ScoutCrawler:
    """
    Advanced web crawling utility for Scout library.
    """
    def __init__(self, base_url: str, max_depth: int = 3, max_pages: int = 50):
        """
        Initialize the web crawler.
        
        Args:
            base_url (str): Starting URL to crawl
            max_depth (int, optional): Maximum crawl depth
            max_pages (int, optional): Maximum number of pages to crawl
        """
        self.base_url = base_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited_urls = set()
        self.crawled_pages = []
        
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid and within the same domain.
        
        Args:
            url (str): URL to validate
        
        Returns:
            bool: Whether the URL is valid
        """
        try:
            parsed_base = urllib.parse.urlparse(self.base_url)
            parsed_url = urllib.parse.urlparse(url)
            
            return (
                parsed_url.scheme in ['http', 'https'] and
                parsed_base.netloc == parsed_url.netloc and
                len(self.visited_urls) < self.max_pages
            )
        except Exception:
            return False
    
    def _crawl_page(self, url: str, depth: int = 0) -> Dict[str, Union[str, List[str]]]:
        """
        Crawl a single page and extract information.
        
        Args:
            url (str): URL to crawl
            depth (int, optional): Current crawl depth
        
        Returns:
            Dict[str, Union[str, List[str]]]: Crawled page information
        """
        if depth > self.max_depth or url in self.visited_urls:
            return {}
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            scout = Scout(response.text, features='lxml')
            
            page_info = {
                'url': url,
                'title': scout.find('title').get_text() if scout.find('title') else '',
                'links': [
                    urllib.parse.urljoin(url, link.get('href')) 
                    for link in scout.find_all('a', href=True) 
                    if self._is_valid_url(urllib.parse.urljoin(url, link.get('href')))
                ],
                'text': scout.get_text(),
                'markdown': scout.to_markdown()
            }
            
            self.visited_urls.add(url)
            self.crawled_pages.append(page_info)
            
            return page_info
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return {}
    
    def crawl(self) -> List[Dict[str, Union[str, List[str]]]]:
        """
        Start web crawling from base URL.
        
        Returns:
            List[Dict[str, Union[str, List[str]]]]: List of crawled pages
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self._crawl_page, self.base_url, 0)}
            
            while futures:
                done, futures = concurrent.futures.wait(
                    futures, return_when=concurrent.futures.FIRST_COMPLETED
                )
                
                for future in done:
                    page_info = future.result()
                    
                    for link in page_info.get('links', []):
                        if link not in self.visited_urls:
                            futures.add(
                                executor.submit(
                                    self._crawl_page, 
                                    link, 
                                    self.visited_urls.count(self.base_url) + 1
                                )
                            )
        
        return self.crawled_pages

class Scout:
    """
    Scout - Making web scraping a breeze! 🌊
    A comprehensive HTML parsing and traversal library.
    Enhanced with advanced features and intelligent parsing.
    """
    
    # Available parsers - choose your weapon! ⚔️
    PARSERS = {
        'html.parser': HTMLParser,
        'lxml': LXMLParser,
        'html5lib': HTML5Parser,
        'lxml-xml': LXMLParser,  # For XML parsing
    }
    
    def __init__(self, markup="", features='html.parser', from_encoding=None, **kwargs):
        """
        Initialize Scout with HTML content.
        
        Args:
            markup (str): HTML content to parse
            features (str): Parser to use ('html.parser', 'lxml', 'html5lib', 'lxml-xml')
            from_encoding (str): Source encoding (if known)
            **kwargs: Additional parsing options
        """
        # Intelligent markup handling
        self.markup = self._preprocess_markup(markup, from_encoding)
        self.features = features
        self.from_encoding = from_encoding
        
        # Get the right parser for the job
        if features not in self.PARSERS:
            raise ValueError(
                f"Invalid parser '{features}'! Choose from: {', '.join(self.PARSERS.keys())}"
            )
        
        parser_class = self.PARSERS[features]
        self.parser = parser_class()
        
        # Parse that HTML! 🎯
        self._soup = self.parser.parse(self.markup)
        
        # BeautifulSoup-like attributes
        self.name = self._soup.name if hasattr(self._soup, 'name') else None
        self.attrs = self._soup.attrs if hasattr(self._soup, 'attrs') else {}
        
        # Advanced parsing options
        self._cache = {}
        
        # Text and web analyzers
        self.text_analyzer = ScoutTextAnalyzer()
        self.web_analyzer = ScoutWebAnalyzer()
    
    def normalize_text(self, text: str, form='NFKD') -> str:
        """
        Normalize text using Unicode normalization.
        
        Args:
            text (str): Input text
            form (str, optional): Normalization form
        
        Returns:
            str: Normalized text
        """
        return unicodedata.normalize(form, text)
    
    def url_parse(self, url: str) -> Dict[str, str]:
        """
        Parse and analyze a URL.
        
        Args:
            url (str): URL to parse
        
        Returns:
            Dict[str, str]: Parsed URL components
        """
        parsed = urllib.parse.urlparse(url)
        return {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
            'params': parsed.params,
            'query': parsed.query,
            'fragment': parsed.fragment
        }
    
    def analyze_page_structure(self) -> Dict[str, Any]:
        """
        Analyze the structure of the parsed page.
        
        Returns:
            Dict[str, Any]: Page structure analysis
        """
        return self.web_analyzer.analyze_page_structure(self)
    
    def analyze_text(self, text: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform advanced text analysis.
        
        Args:
            text (str, optional): Text to analyze. If None, uses page text.
        
        Returns:
            Dict[str, Any]: Text analysis results
        """
        if text is None:
            text = self.get_text()
        
        return {
            'word_count': self.text_analyzer.count_words(text),
            'entities': self.text_analyzer.extract_entities(text),
            'tokens': self.text_analyzer.tokenize(text)
        }
    
    def extract_semantic_info(self) -> Dict[str, Any]:
        """
        Extract semantic information from the document.
        
        Returns:
            Dict[str, Any]: Semantic information
        """
        semantic_info = {
            'headings': {
                'h1': [h.get_text(strip=True) for h in self.find_all('h1')],
                'h2': [h.get_text(strip=True) for h in self.find_all('h2')],
                'h3': [h.get_text(strip=True) for h in self.find_all('h3')]
            },
            'lists': {
                'ul': [ul.find_all('li') for ul in self.find_all('ul')],
                'ol': [ol.find_all('li') for ol in self.find_all('ol')]
            },
            'tables': {
                'count': len(self.find_all('table')),
                'headers': [table.find_all('th') for table in self.find_all('table')]
            }
        }
        return semantic_info
    
    def cache(self, key: str, value: Any = None) -> Any:
        """
        Manage a cache for parsed content.
        
        Args:
            key (str): Cache key
            value (Any, optional): Value to cache
        
        Returns:
            Any: Cached value or None
        """
        if value is not None:
            self._cache[key] = value
        return self._cache.get(key)
    
    def hash_content(self, method='md5') -> str:
        """
        Generate a hash of the parsed content.
        
        Args:
            method (str, optional): Hashing method
        
        Returns:
            str: Content hash
        """
        hash_methods = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256
        }
        
        if method not in hash_methods:
            raise ValueError(f"Unsupported hash method: {method}")
        
        hasher = hash_methods[method]()
        hasher.update(str(self._soup).encode('utf-8'))
        return hasher.hexdigest()
    
    def extract_links(self, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extract all links from the document.
        
        Args:
            base_url (str, optional): Base URL for resolving relative links
        
        Returns:
            List[Dict[str, str]]: List of link dictionaries
        """
        links = []
        for link in self.find_all(['a', 'link']):
            href = link.get('href')
            if href:
                # Resolve relative URLs if base_url is provided
                if base_url and not href.startswith(('http://', 'https://', '//')):
                    href = f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                
                links.append({
                    'href': href,
                    'text': link.get_text(strip=True),
                    'rel': link.get('rel', [None])[0],
                    'type': link.get('type')
                })
        return links
    
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from HTML document.
        
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        metadata = {
            'title': self.find('title').get_text() if self.find('title') else None,
            'description': self.find('meta', attrs={'name': 'description'}).get('content') if self.find('meta', attrs={'name': 'description'}) else None,
            'keywords': self.find('meta', attrs={'name': 'keywords'}).get('content', '').split(',') if self.find('meta', attrs={'name': 'keywords'}) else [],
            'og_metadata': {},
            'twitter_metadata': {}
        }
        
        # Open Graph metadata
        for meta in self.find_all('meta', attrs={'property': re.compile(r'^og:')}):
            key = meta.get('property')[3:]
            metadata['og_metadata'][key] = meta.get('content')
        
        # Twitter Card metadata
        for meta in self.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
            key = meta.get('name')[8:]
            metadata['twitter_metadata'][key] = meta.get('content')
        
        return metadata
    
    def to_json(self, indent=2) -> str:
        """
        Convert parsed content to JSON.
        
        Args:
            indent (int, optional): JSON indentation
        
        Returns:
            str: JSON representation of the document
        """
        def _tag_to_dict(tag):
            if isinstance(tag, NavigableString):
                return str(tag)
            
            result = {
                'name': tag.name,
                'attrs': tag.attrs,
                'text': tag.get_text(strip=True)
            }
            
            if tag.contents:
                result['children'] = [_tag_to_dict(child) for child in tag.contents]
            
            return result
        
        return json.dumps(_tag_to_dict(self._soup), indent=indent)
    
    def find(self, name=None, attrs={}, recursive=True, text=None, **kwargs) -> Optional[Tag]:
        """
        Find the first matching element.
        
        Args:
            name (str, optional): Tag name to search for
            attrs (dict, optional): Attributes to match
            recursive (bool, optional): Search recursively
            text (str, optional): Text content to match
        
        Returns:
            Tag or None: First matching element
        """
        result = self._soup.find(name, attrs, recursive, text, **kwargs)
        return ScoutSearchResult([result]) if result else ScoutSearchResult([])
    
    def find_all(self, name=None, attrs={}, recursive=True, text=None, limit=None, **kwargs) -> ScoutSearchResult:
        """
        Find all matching elements.
        
        Args:
            name (str, optional): Tag name to search for
            attrs (dict, optional): Attributes to match
            recursive (bool, optional): Search recursively
            text (str, optional): Text content to match
            limit (int, optional): Maximum number of results
        
        Returns:
            ScoutSearchResult: List of matching elements
        """
        results = self._soup.find_all(name, attrs, recursive, text, limit, **kwargs)
        return ScoutSearchResult(results)
    
    def find_parent(self, name=None, attrs={}, **kwargs):
        """
        Find the first parent matching given criteria.
        
        Args:
            name (str, optional): Tag name to search for
            attrs (dict, optional): Attributes to match
        
        Returns:
            Tag or None: First matching parent
        """
        current = self._soup.parent
        while current:
            if (name is None or current.name == name) and \
               all(current.get(k) == v for k, v in attrs.items()):
                return current
            current = current.parent
        return None
    
    def find_parents(self, name=None, attrs={}, limit=None, **kwargs):
        """
        Find all parents matching given criteria.
        
        Args:
            name (str, optional): Tag name to search for
            attrs (dict, optional): Attributes to match
            limit (int, optional): Maximum number of results
        
        Returns:
            List[Tag]: List of matching parents
        """
        parents = []
        current = self._soup.parent
        while current and (limit is None or len(parents) < limit):
            if (name is None or current.name == name) and \
               all(current.get(k) == v for k, v in attrs.items()):
                parents.append(current)
            current = current.parent
        return parents
    
    def find_next_sibling(self, name=None, attrs={}, **kwargs):
        """
        Find the next sibling matching given criteria.
        
        Args:
            name (str, optional): Tag name to search for
            attrs (dict, optional): Attributes to match
        
        Returns:
            Tag or None: First matching next sibling
        """
        if not self._soup.parent:
            return None
        
        siblings = self._soup.parent.contents
        try:
            current_index = siblings.index(self._soup)
            for sibling in siblings[current_index + 1:]:
                if isinstance(sibling, Tag):
                    if (name is None or sibling.name == name) and \
                       all(sibling.get(k) == v for k, v in attrs.items()):
                        return sibling
        except ValueError:
            pass
        return None
    
    def find_next_siblings(self, name=None, attrs={}, limit=None, **kwargs):
        """
        Find all next siblings matching given criteria.
        
        Args:
            name (str, optional): Tag name to search for
            attrs (dict, optional): Attributes to match
            limit (int, optional): Maximum number of results
        
        Returns:
            List[Tag]: List of matching next siblings
        """
        if not self._soup.parent:
            return []
        
        siblings = []
        siblings_list = self._soup.parent.contents
        try:
            current_index = siblings_list.index(self._soup)
            for sibling in siblings_list[current_index + 1:]:
                if isinstance(sibling, Tag):
                    if (name is None or sibling.name == name) and \
                       all(sibling.get(k) == v for k, v in attrs.items()):
                        siblings.append(sibling)
                        if limit and len(siblings) == limit:
                            break
        except ValueError:
            pass
        return siblings
    
    def select(self, selector: str) -> List[Tag]:
        """
        Select elements using CSS selector.
        
        Args:
            selector (str): CSS selector string
        
        Returns:
            List[Tag]: List of matching elements
        """
        return self._soup.select(selector)
    
    def select_one(self, selector: str) -> Optional[Tag]:
        """
        Select the first element matching the CSS selector.
        
        Args:
            selector (str): CSS selector string
        
        Returns:
            Tag or None: First matching element
        """
        return self._soup.select_one(selector)
    
    def get_text(self, separator=' ', strip=False, types=None) -> str:
        """
        Extract all text from the parsed document.
        
        Args:
            separator (str, optional): Text separator
            strip (bool, optional): Strip whitespace
            types (list, optional): Types of content to extract
        
        Returns:
            str: Extracted text
        """
        return self._soup.get_text(separator, strip, types)
    
    def prettify(self, formatter='minimal') -> str:
        """
        Return a formatted, pretty-printed version of the HTML.
        
        Args:
            formatter (str, optional): Formatting style
        
        Returns:
            str: Prettified HTML
        """
        return self._soup.prettify(formatter)
    
    def decompose(self, tag: Tag = None) -> None:
        """
        Remove a tag and its contents from the document.
        
        Args:
            tag (Tag, optional): Tag to remove. If None, removes the root tag.
        """
        if tag is None:
            tag = self._soup
        tag.decompose()
    
    def extract(self, tag: Tag = None) -> Tag:
        """
        Remove a tag from the document and return it.
        
        Args:
            tag (Tag, optional): Tag to extract. If None, extracts the root tag.
        
        Returns:
            Tag: Extracted tag
        """
        if tag is None:
            tag = self._soup
        return tag.extract()
    
    def clear(self, tag: Tag = None) -> None:
        """
        Remove a tag's contents while keeping the tag itself.
        
        Args:
            tag (Tag, optional): Tag to clear. If None, clears the root tag.
        """
        if tag is None:
            tag = self._soup
        tag.clear()
    
    def replace_with(self, old_tag: Tag, new_tag: Tag) -> None:
        """
        Replace one tag with another.
        
        Args:
            old_tag (Tag): Tag to replace
            new_tag (Tag): Replacement tag
        """
        old_tag.replace_with(new_tag)
    
    def encode(self, encoding='utf-8') -> bytes:
        """
        Encode the document to a specific encoding.
        
        Args:
            encoding (str, optional): Encoding to use
        
        Returns:
            bytes: Encoded document
        """
        return str(self._soup).encode(encoding)
    
    def decode(self, encoding='utf-8') -> str:
        """
        Decode the document from a specific encoding.
        
        Args:
            encoding (str, optional): Encoding to use
        
        Returns:
            str: Decoded document
        """
        return str(self._soup)
    
    def __str__(self) -> str:
        """
        String representation of the parsed document.
        
        Returns:
            str: HTML content
        """
        return str(self._soup)
    
    def __repr__(self) -> str:
        """
        Detailed representation of the Scout object.
        
        Returns:
            str: Scout object description
        """
        return f"Scout(features='{self.features}', content_length={len(self.markup)})"

    def _preprocess_markup(self, markup: str, encoding: Optional[str] = None) -> str:
        """
        Preprocess markup before parsing.
        
        Args:
            markup (str): Input markup
            encoding (str, optional): Encoding to use
        
        Returns:
            str: Preprocessed markup
        """
        # Decode markup
        decoded_markup = decode_markup(markup, encoding)
        
        # Basic HTML cleaning
        # Remove comments, normalize whitespace, etc.
        decoded_markup = re.sub(r'<!--.*?-->', '', decoded_markup, flags=re.DOTALL)
        decoded_markup = re.sub(r'\s+', ' ', decoded_markup)
        
        return decoded_markup

    def to_markdown(self, heading_style='ATX') -> str:
        """
        Convert HTML to Markdown.
        
        Args:
            heading_style (str, optional): Markdown heading style
        
        Returns:
            str: Markdown representation of the document
        """
        converter = MarkdownConverter(heading_style=heading_style)
        return converter.convert(str(self._soup))
