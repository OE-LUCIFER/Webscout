import requests
from typing import Dict, List, Optional, Union, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from webscout.scout import Scout
from urllib.parse import quote, urljoin
from webscout.litagent import LitAgent

import time
import random
import json
import os
from datetime import datetime, timedelta
from functools import lru_cache
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme

class GoogleS:
    """A Python interface for Google search with advanced features

    The GoogleS class provides a powerful interface to perform web searches, image searches,
    and advanced filtering on Google. Built with love by HAI to keep it

    Basic Usage:
        >>> from webscout.DWEBS import GoogleS
        >>> searcher = GoogleS()
        >>> # Simple web search
        >>> results = searcher.search("Python programming")
        >>> for result in results:
        ...     print(f"Title: {result['title']}")
        ...     print(f"URL: {result['href']}")
        ...     print(f"Description: {result['abstract']}")

    Advanced Web Search:
        >>> # Search with filters
        >>> results = searcher.search(
        ...     query="Python tutorials",
        ...     site="github.com",
        ...     file_type="pdf",
        ...     time_period="month",
        ...     max_results=5
        ... )
        >>> # Example response format:
        >>> {
        ...     'title': 'Python Tutorial',
        ...     'href': 'https://example.com/python-tutorial',
        ...     'abstract': 'Comprehensive Python tutorial covering basics to advanced topics',
        ...     'index': 0,
        ...     'type': 'web',
        ...     'visible_text': ''  # Optional: Contains webpage text if extract_text=True
        ... }

    Image Search:
        >>> # Search for images
        >>> images = searcher.search_images(
        ...     query="cute puppies",
        ...     size="large",
        ...     color="color",
        ...     type_filter="photo",
        ...     max_results=5
        ... )
        >>> # Example response format:
        >>> {
        ...     'title': 'Cute Puppy Image',
        ...     'thumbnail': 'https://example.com/puppy-thumb.jpg',
        ...     'full_url': 'https://example.com/puppy-full.jpg',
        ...     'type': 'image'
        ... }

    Features:
        - Web Search: Get detailed web results with title, URL, and description
        - Image Search: Find images with thumbnails and full-resolution URLs
        - Advanced Filters: Site-specific search, file types, time periods
        - Rate Limiting: Smart request handling to avoid blocks
        - Caching: Save results for faster repeat searches
        - Retry Logic: Automatic retry on temporary failures
        - Logging: Optional LitLogger integration for beautiful console output
        - Proxy Support: Use custom proxies for requests
        - Concurrent Processing: Multi-threaded requests for better performance

    Response Format:
        Web Search Results:
            {
                'title': str,       # Title of the webpage
                'href': str,        # URL of the webpage
                'abstract': str,    # Brief description or snippet
                'index': int,       # Result position
                'type': 'web',      # Result type identifier
                'visible_text': str # Full page text (if extract_text=True)
            }

        Image Search Results:
            {
                'title': str,       # Image title or description
                'thumbnail': str,   # Thumbnail image URL
                'full_url': str,    # Full resolution image URL
                'type': 'image'     # Result type identifier
            }
    """

    SEARCH_TYPES = {
        "web": "https://www.google.com/search",
        "image": "https://www.google.com/images",
        "news": "https://www.google.com/news",
    }

    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = 10,
        max_workers: int = 20,
        cache_dir: Optional[str] = None,
        rate_limit: float = 0.01,
        use_litlogger: bool = False
    ):
        """
        Initialize the GoogleS object with enhanced features.
        
        Args:
            cache_dir: Directory to store search result cache
            rate_limit: Minimum time between requests in seconds
            use_litlogger: Whether to use LitLogger for logging (default: False)
        """
        self.proxy = proxy
        self.headers = headers if headers else {
            "User-Agent": LitAgent().random()  # Use LitAgent to generate user agent
        }
        self.headers["Referer"] = "https://www.google.com/"
        self.client = requests.Session()
        self.client.headers.update(self.headers)
        if proxy:
            self.client.proxies.update({"http": proxy, "https": proxy})
        self.timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.cache_dir = cache_dir
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.last_request_time = 0
        self.rate_limit = rate_limit
        self.use_litlogger = use_litlogger
        
        # Setup enhanced logging with LitLogger if enabled
        if self.use_litlogger:
            self.logger = LitLogger(
                name="GoogleS",
                format=LogFormat.MODERN_EMOJI,
                color_scheme=ColorScheme.CYBERPUNK,
                console_output=True
            )

    def _respect_rate_limit(self):
        """Ensure minimum time between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()

    def _get_url(self, method: str, url: str, params: Optional[Dict[str, str]] = None,
                  data: Optional[Union[Dict[str, str], bytes]] = None, max_retries: int = 3) -> bytes:
        """
        Makes an HTTP request with manual retry logic and rate limiting.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            url (str): Target URL
            params (Optional[Dict[str, str]]): Query parameters
            data (Optional[Union[Dict[str, str], bytes]]): Request payload
            max_retries (int): Maximum number of retry attempts
        
        Returns:
            bytes: Response content
        """
        self._respect_rate_limit()
        
        for attempt in range(max_retries):
            try:
                if self.use_litlogger:
                    self.logger.debug(f"Making {method} request to {url} (Attempt {attempt + 1})")
                
                resp = self.client.request(method, url, params=params, data=data, timeout=self.timeout)
                resp.raise_for_status()
                
                if self.use_litlogger:
                    self.logger.success(f"Request successful: {resp.status_code}")
                
                return resp.content
            
            except requests.exceptions.RequestException as ex:
                if self.use_litlogger:
                    self.logger.error(f"Request failed: {url} - {str(ex)}")
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.random()
                    time.sleep(wait_time)
                else:
                    raise

    @lru_cache(maxsize=100)
    def _cache_key(self, query: str, **kwargs) -> str:
        """Generate a cache key from search parameters"""
        cache_data = {'query': query, **kwargs}
        return json.dumps(cache_data, sort_keys=True)

    def _get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached results if they exist and are not expired"""
        if not self.cache_dir:
            return None
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                if datetime.fromisoformat(cached_data['timestamp']) + timedelta(hours=24) > datetime.now():
                    if self.use_litlogger:
                        self.logger.info(f"Using cached results for: {cache_key}")
                    return cached_data['results']
        if self.use_litlogger:
            self.logger.debug(f"No valid cache found for: {cache_key}")
        return None

    def _cache_results(self, cache_key: str, results: List[Dict[str, Any]]):
        """Cache search results"""
        if not self.cache_dir:
            return
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f)

    def search_images(
        self,
        query: str,
        max_results: int = 10,
        size: Optional[str] = None,
        color: Optional[str] = None,
        type_filter: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, str]]:
        """Search for images on Google with style! 

        Args:
            query (str): What you're looking for fam
            max_results (int): How many results you want (default: 10)
            size (Optional[str]): Image size filter
                - 'large': Big pics
                - 'medium': Medium sized
                - 'icon': Small icons
            color (Optional[str]): Color filter
                - 'color': Full color
                - 'gray': Black and white
                - 'transparent': Transparent background
            type_filter (Optional[str]): Type of image
                - 'face': Just faces
                - 'photo': Real photos
                - 'clipart': Vector art
                - 'lineart': Line drawings

        Returns:
            List[Dict[str, str]]: List of image results with these keys:
                - 'thumbnail': Small preview URL
                - 'full_url': Full resolution image URL
                - 'title': Image title/description
                - 'type': Always 'image'

        Example:
            >>> searcher = GoogleS()
            >>> # Find some cool nature pics
            >>> images = searcher.search_images(
            ...     query="beautiful landscapes",
            ...     size="large",
            ...     color="color",
            ...     max_results=5
            ... )
            >>> for img in images:
            ...     print(f"Found: {img['title']}")
            ...     print(f"URL: {img['full_url']}")
        """
        params = {
            "q": query,
            "tbm": "isch",
            "num": max_results
        }
        
        if size:
            params["tbs"] = f"isz:{size}"
        if color:
            params["tbs"] = f"ic:{color}"
        if type_filter:
            params["tbs"] = f"itp:{type_filter}"

        content = self._get_url("GET", self.SEARCH_TYPES["image"], params=params)
        soup = Scout(content)  # Use Scout parser
        
        results = []
        for img in soup.find_all("img", class_="rg_i"):
            if len(results) >= max_results:
                break
            
            img_data = {
                "thumbnail": img.get("src", ""),
                "title": img.get("alt", ""),
                "type": "image"
            }
            
            # Extract full resolution image URL if available
            parent = img.parent
            if parent and parent.get("href"):
                img_data["full_url"] = urljoin("https://www.google.com", parent["href"])
            
            results.append(img_data)
            
        return results

    def search(
        self,
        query: str,
        region: str = "us-en",
        language: str = "en",
        safe: str = "off",
        time_period: Optional[str] = None,
        max_results: int = 10,
        extract_text: bool = False,
        max_text_length: Optional[int] = 100,
        site: Optional[str] = None,  # Search within specific site
        file_type: Optional[str] = None,  # Filter by file type
        sort_by: str = "relevance",  # relevance, date
        exclude_terms: Optional[List[str]] = None,  # Terms to exclude
        exact_phrase: Optional[str] = None,  # Exact phrase match
    ) -> List[Dict[str, Union[str, int]]]:
        """
        Enhanced search with additional filters and options.
        
        Args:
            site: Limit search to specific website
            file_type: Filter by file type (pdf, doc, etc.)
            sort_by: Sort results by relevance or date
            exclude_terms: List of terms to exclude from search
            exact_phrase: Exact phrase to match
        """
        if self.use_litlogger:
            self.logger.info(f"Starting search for: {query}")
        
        # Build advanced query
        advanced_query = query
        if site:
            advanced_query += f" site:{site}"
        if file_type:
            advanced_query += f" filetype:{file_type}"
        if exclude_terms:
            advanced_query += " " + " ".join(f"-{term}" for term in exclude_terms)
        if exact_phrase:
            advanced_query = f'"{exact_phrase}"' + advanced_query
            
        if self.use_litlogger:
            self.logger.debug(f"Advanced query: {advanced_query}")
        
        # Check cache first
        cache_key = self._cache_key(advanced_query, region=region, language=language,
                                  safe=safe, time_period=time_period, sort_by=sort_by)
        cached_results = self._get_cached_results(cache_key)
        if cached_results:
            return cached_results[:max_results]

        # Continue with regular search implementation...
        results = []
        futures = []
        start = 0

        while len(results) < max_results:
            params = {
                "q": advanced_query,
                "num": 10,
                "hl": language,
                "start": start,
                "safe": safe,
                "gl": region,
            }
            if time_period:
                params["tbs"] = f"qdr:{time_period}"

            futures.append(self._executor.submit(self._get_url, "GET", self.SEARCH_TYPES["web"], params=params))
            start += 10

            for future in as_completed(futures):
                try:
                    resp_content = future.result()
                    soup = Scout(resp_content)  # Use Scout parser
                    
                    result_blocks = soup.find_all("div", class_="g")

                    if not result_blocks:
                        break

                    # Extract links and titles first
                    for result_block in result_blocks:
                        link = result_block.find("a", href=True)
                        title = result_block.find("h3")
                        description_box = result_block.find(
                            "div", {"style": "-webkit-line-clamp:2"}
                        )

                        if link and title and description_box:
                            url = link["href"]
                            results.append({
                                "title": title.text,
                                "href": url,
                                "abstract": description_box.text,
                                "index": len(results),
                                "type": "web",
                                "visible_text": ""  # Initialize visible_text as empty string
                            })

                            if len(results) >= max_results:
                                break  # Stop if we have enough results

                    # Parallelize text extraction if needed
                    if extract_text:
                        with ThreadPoolExecutor(max_workers=self._executor._max_workers) as text_extractor:
                            extraction_futures = [
                                text_extractor.submit(self._extract_text_from_webpage, 
                                                    self._get_url("GET", result['href']),
                                                    max_characters=max_text_length)
                                for result in results 
                                if 'href' in result
                            ]
                            for i, future in enumerate(as_completed(extraction_futures)):
                                try:
                                    results[i]['visible_text'] = future.result()
                                except Exception as e:
                                    print(f"Error extracting text: {e}")

                except Exception as e:
                    print(f"Error: {e}")  

        # Cache results before returning
        self._cache_results(cache_key, results)
        return results

    def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions for a query"""
        params = {
            "client": "chrome",
            "q": query
        }
        content = self._get_url("GET", "https://suggestqueries.google.com/complete/search",
                               params=params)
        suggestions = json.loads(content.decode('utf-8'))[1]
        return suggestions

    def _extract_text_from_webpage(self, html_content: bytes, max_characters: Optional[int] = None) -> str:
        """
        Extracts visible text from HTML content using Scout parser.
        """
        soup = Scout(html_content)  # Use Scout parser
        for tag in soup(["script", "style", "header", "footer", "nav"]):
            tag.extract()
        visible_text = soup.get_text(strip=True)
        if max_characters:
            visible_text = visible_text[:max_characters]
        return visible_text

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        self._executor.shutdown()


if __name__ == "__main__":
    from rich import print
    searcher = GoogleS()
    results = searcher.search("HelpingAI-9B", max_results=200, extract_text=False, max_text_length=200)
    for result in results:
        print(result)