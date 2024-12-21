"""
Scout Crawler Module
"""

import concurrent.futures
import urllib.parse
from typing import Union, List, Dict
import requests

from .scout import Scout

class ScoutCrawler:
    """
    Advanced web crawling utility for Scout library.
    """
    def __init__(self, base_url: str, max_pages: int = 50, tags_to_remove: List[str] = None):
        """
        Initialize the web crawler.
        
        Args:
            base_url (str): Starting URL to crawl
            max_pages (int, optional): Maximum number of pages to crawl
            tags_to_remove (List[str], optional): List of tags to remove
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.tags_to_remove = tags_to_remove if tags_to_remove is not None else ["script", "style", "header", "footer", "nav", "aside", "form", "button"]
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
        if url in self.visited_urls:
            return {}
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            scout = Scout(response.content, features='lxml')
            
            title_result = scout.find('title')
            title = title_result[0].get_text() if title_result else ''
            
            visible_text = scout._soup.get_text(strip=True)
            
            for tag in scout._soup(self.tags_to_remove):
                tag.extract()
            
            page_info = {
                'url': url,
                'title': title,
                'links': [
                    urllib.parse.urljoin(url, link.get('href')) 
                    for link in scout.find_all('a', href=True) 
                    if self._is_valid_url(urllib.parse.urljoin(url, link.get('href')))
                ],
                'text': visible_text,
                'depth': depth
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
                    
                    if len(self.visited_urls) >= self.max_pages:
                        break
                    
                    submitted_links = set()  # New set to track submitted links
                    for link in page_info.get('links', []):
                        if (
                            len(self.visited_urls) < self.max_pages and
                            link not in self.visited_urls
                        ):
                            if link not in submitted_links:  # Check against submitted links
                                submitted_links.add(link)  # Add to submitted links
                                futures.add(
                                    executor.submit(
                                        self._crawl_page,
                                        link,
                                        page_info.get('depth', 0) + 1
                                    )
                                )
                    if len(self.visited_urls) >= self.max_pages:
                        break
        
        return self.crawled_pages
