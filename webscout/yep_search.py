import cloudscraper
from urllib.parse import urlencode
from webscout.litagent import LitAgent
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import json
class YepSearch:
    """Yep.com search class to get search results."""
    
    _executor: ThreadPoolExecutor = ThreadPoolExecutor()

    def __init__(
        self,
        timeout: int = 20,
        proxies: Dict[str, str] | None = None,
        verify: bool = True,
    ):
        """Initialize YepSearch.
        
        Args:
            timeout: Timeout value for the HTTP client. Defaults to 20.
            proxies: Proxy configuration for requests. Defaults to None.
            verify: Verify SSL certificates. Defaults to True.
        """
        self.base_url = "https://api.yep.com/fs/2/search"
        self.timeout = timeout
        self.session = cloudscraper.create_scraper()
        self.session.headers.update({
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "DNT": "1",
            "Origin": "https://yep.com",
            "Referer": "https://yep.com/",
            "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": LitAgent().random()
        })
        if proxies:
            self.session.proxies.update(proxies)
        self.session.verify = verify

    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text using simple string manipulation.
        
        Args:
            text: String containing HTML tags
            
        Returns:
            Clean text without HTML tags
        """
        result = ""
        in_tag = False
        
        for char in text:
            if char == '<':
                in_tag = True
            elif char == '>':
                in_tag = False
            elif not in_tag:
                result += char
                
        # Replace common HTML entities
        replacements = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
        }
        
        for entity, replacement in replacements.items():
            result = result.replace(entity, replacement)
            
        return result.strip()

    def format_results(self, raw_results: dict) -> List[Dict]:
        """Format raw API results into a consistent structure."""
        formatted_results = []
        
        if not raw_results or len(raw_results) < 2:
            return formatted_results

        results = raw_results[1].get('results', [])
        
        for result in results:
            formatted_result = {
                "title": self._remove_html_tags(result.get("title", "")),
                "href": result.get("url", ""),
                "body": self._remove_html_tags(result.get("snippet", "")),
                "source": result.get("visual_url", ""),
                "position": len(formatted_results) + 1,
                "type": result.get("type", "organic"),
                "first_seen": result.get("first_seen", None)
            }
            
            # Add sitelinks if they exist
            if "sitelinks" in result:
                sitelinks = []
                if "full" in result["sitelinks"]:
                    sitelinks.extend(result["sitelinks"]["full"])
                if "short" in result["sitelinks"]:
                    sitelinks.extend(result["sitelinks"]["short"])
                
                if sitelinks:
                    formatted_result["sitelinks"] = [
                        {
                            "title": self._remove_html_tags(link.get("title", "")),
                            "href": link.get("url", "")
                        }
                        for link in sitelinks
                    ]
            
            formatted_results.append(formatted_result)
        
        return formatted_results

    def text(
        self,
        keywords: str,
        region: str = "all",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """Yep.com text search.

        Args:
            keywords: Search query string.
            region: Region for search results. Defaults to "all".
            safesearch: SafeSearch setting ("on", "moderate", "off"). Defaults to "moderate".
            max_results: Maximum number of results to return. Defaults to None.

        Returns:
            List of dictionaries containing search results.
        """
        # Convert safesearch parameter
        safe_search_map = {
            "on": "on",
            "moderate": "moderate",
            "off": "off"
        }
        safe_setting = safe_search_map.get(safesearch.lower(), "moderate")

        params = {
            "client": "web",
            "gl": region,
            "limit": str(max_results) if max_results else "10",
            "no_correct": "false",
            "q": keywords,
            "safeSearch": safe_setting,
            "type": "web"
        }
        
        url = f"{self.base_url}?{urlencode(params)}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            raw_results = response.json()
            
            formatted_results = self.format_results(raw_results)
            
            if max_results:
                return formatted_results[:max_results]
            return formatted_results
        except Exception as e:
            raise Exception(f"Yep search failed: {str(e)}")

    def images(
        self,
        keywords: str,
        region: str = "all",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """Yep.com image search.

        Args:
            keywords: Search query string.
            region: Region for search results. Defaults to "all".
            safesearch: SafeSearch setting ("on", "moderate", "off"). Defaults to "moderate".
            max_results: Maximum number of results to return. Defaults to None.

        Returns:
            List of dictionaries containing image search results with keys:
            - title: Image title
            - image: Full resolution image URL
            - thumbnail: Thumbnail image URL
            - url: Source page URL
            - height: Image height
            - width: Image width
            - source: Source website domain
        """
        safe_search_map = {
            "on": "on",
            "moderate": "moderate",
            "off": "off"
        }
        safe_setting = safe_search_map.get(safesearch.lower(), "moderate")

        params = {
            "client": "web",
            "gl": region,
            "limit": str(max_results) if max_results else "10",
            "no_correct": "false",
            "q": keywords,
            "safeSearch": safe_setting,
            "type": "images"
        }
        
        url = f"{self.base_url}?{urlencode(params)}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            raw_results = response.json()
            
            if not raw_results or len(raw_results) < 2:
                return []

            formatted_results = []
            results = raw_results[1].get('results', [])
            
            for result in results:
                if result.get("type") != "Image":
                    continue
                
                formatted_result = {
                    "title": self._remove_html_tags(result.get("title", "")),
                    "image": result.get("image_id", ""),
                    "thumbnail": result.get("src", ""),
                    "url": result.get("host_page", ""),
                    "height": result.get("height", 0),
                    "width": result.get("width", 0),
                    "source": result.get("visual_url", "")
                }
                
                # Add high-res thumbnail if available
                if "srcset" in result:
                    formatted_result["thumbnail_hd"] = result["srcset"].split(",")[1].strip().split(" ")[0]
                
                formatted_results.append(formatted_result)
            
            if max_results:
                return formatted_results[:max_results]
            return formatted_results
        
        except Exception as e:
            raise Exception(f"Yep image search failed: {str(e)}")

    def suggestions(
        self,
        query: str,
        region: str = "all",
    ) -> List[str]:
        """Get search suggestions from Yep.com autocomplete API.

        Args:
            query: Search query string to get suggestions for.
            region: Region for suggestions. Defaults to "all".

        Returns:
            List of suggestion strings.

        Example:
            >>> yep = YepSearch()
            >>> suggestions = yep.suggestions("ca")
            >>> print(suggestions)
            ['capital one', 'car wash', 'carmax', 'cafe', ...]
        """
        params = {
            "query": query,
            "type": "web",
            "gl": region
        }
        
        url = f"https://api.yep.com/ac/?{urlencode(params)}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            # Return suggestions list if response format is valid
            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                return data[1]
            return []
        
        except Exception as e:
            raise Exception(f"Yep suggestions failed: {str(e)}")


if __name__ == "__main__":
    yep = YepSearch()
    r = yep.suggestions("hi", region="all")
    print(r)
