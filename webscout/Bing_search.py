from bs4 import BeautifulSoup
import requests
from typing import Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from termcolor import colored
import time
import random

class BingS:
    """Bing search class to get search results from bing.com."""

    _executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=10)

    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = 10,
    ) -> None:
        """Initialize the BingS object."""
        self.proxy: Optional[str] = proxy
        self.headers = headers if headers else {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62"
        }
        self.headers["Referer"] = "https://www.bing.com/"
        self.client = requests.Session()
        self.client.headers.update(self.headers)
        self.client.proxies.update({"http": self.proxy, "https": self.proxy})
        self.timeout = timeout

    def __enter__(self) -> "BingS":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def _get_url(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, str], bytes]] = None,
    ) -> bytes:
        try:
            resp = self.client.request(method, url, params=params, data=data, timeout=self.timeout)
        except Exception as ex:
            raise Exception(f"{url} {type(ex).__name__}: {ex}") from ex
        if resp.status_code == 200:
            return resp.content
        raise Exception(f"{resp.url} returned status code {resp.status_code}. {params=} {data=}")

    def search(
        self,
        keywords: str,
        region: str = "us-EN",  # Bing uses us-EN
        lang: str = "en",
        safe: str = "off",
        timelimit: Optional[str] = None,  # Not directly supported by Bing
        max_results: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """Bing text search."""
        assert keywords, "keywords is mandatory"

        results = []
        start = 1  # Bing uses 1-based indexing for pages
        while len(results) < (max_results or float('inf')):
            params = {
                "q": keywords,
                "count": 10,  # Number of results per page
                "mkt": region,
                "setlang": lang,
                "safeSearch": safe,
                "first": start,  # Bing uses 'first' for pagination
            }

            try:
                resp_content = self._get_url("GET", "https://www.bing.com/search", params=params)
                soup = BeautifulSoup(resp_content, "html.parser")
                result_block = soup.find_all("li", class_="b_algo")

                if not result_block:
                    break

                for result in result_block:
                    try:
                        link = result.find("a", href=True)
                        if link:
                            initial_url = link["href"]

                            title = result.find("h2").text if result.find("h2") else ""
                            description = result.find("p").text.strip() if result.find("p") else ""  # Strip whitespace

                            # Remove 'WEB' prefix if present
                            if description.startswith("WEB"):
                                description = description[4:]  # Skip the first 4 characters ('WEB ')

                            results.append({
                                "title": title,
                                "href": initial_url,
                                "abstract": description,
                                "index": len(results),
                                "type": "web",
                            })

                            if len(results) >= max_results:
                                return results

                    except Exception as e:
                        print(f"Error extracting result: {e}")

            except Exception as e:
                print(f"Error fetching URL: {e}")

            start += 10

        return results

if __name__ == "__main__":
    from rich import print
    searcher = BingS()
    results = searcher.search("Python development tools", max_results=30)
    for result in results:
        print(result)
