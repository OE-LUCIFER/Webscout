from bs4 import BeautifulSoup
import requests
from typing import Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from termcolor import colored
import time
import random

class GoogleS:
    """Google search class to get search results from google.com."""

    _executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=10)

    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = 10,
    ) -> None:
        """Initialize the GoogleS object."""
        self.proxy: Optional[str] = proxy
        self.headers = headers if headers else {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62"
        }
        self.headers["Referer"] = "https://www.google.com/"
        self.client = requests.Session()
        self.client.headers.update(self.headers)
        self.client.proxies.update({"http": self.proxy, "https": self.proxy})
        self.timeout = timeout

    def __enter__(self) -> "GoogleS":
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

    def extract_text_from_webpage(self, html_content, max_characters=None):
        """Extracts visible text from HTML content using BeautifulSoup."""
        soup = BeautifulSoup(html_content, "html.parser")
        # Remove unwanted tags
        for tag in soup(["script", "style", "header", "footer", "nav"]):
            tag.extract()
        # Get the remaining visible text
        visible_text = soup.get_text(strip=True)
        if max_characters:
            visible_text = visible_text[:max_characters]
        return visible_text

    def search(
        self,
        keywords: str,
        region: str = "us-en",
        lang: str = "en",
        safe: str = "off",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = None,
        extract_webpage_text: bool = False,
        max_extract_characters: Optional[int] = 100,  
    ) -> List[Dict[str, str]]:
        """Google text search."""
        assert keywords, "keywords is mandatory"

        results = []
        futures = []
        start = 0
        while len(results) < max_results:
            params = {
                "q": keywords,
                "num": 10,  # Number of results per page
                "hl": lang,
                "start": start,
                "safe": safe,
                "gl": region,
            }
            if timelimit:
                params["tbs"] = f"qdr:{timelimit}"

            futures.append(self._executor.submit(self._get_url, "GET", "https://www.google.com/search", params=params))
            start += 10

            for future in as_completed(futures):
                try:
                    resp_content = future.result()
                    soup = BeautifulSoup(resp_content, "html.parser")
                    result_block = soup.find_all("div", class_="g")

                    if not result_block:
                        break

                    for result in result_block:
                        try:
                            link = result.find("a", href=True)
                            title = result.find("h3")
                            description_box = result.find(
                                "div", {"style": "-webkit-line-clamp:2"}
                            )

                            if link and title and description_box:
                                url = link["href"]
                                title = title.text
                                description = description_box.text

                                visible_text = ""
                                if extract_webpage_text:
                                    try:
                                        page_content = self._get_url("GET", url)
                                        visible_text = self.extract_text_from_webpage(
                                            page_content, max_characters=max_extract_characters
                                        )
                                    except Exception as e:
                                        print(f"Error extracting text from {url}: {e}")

                                results.append(
                                    {
                                        "title": title,
                                        "href": url,
                                        "abstract": description,
                                        "index": len(results),
                                        "type": "web",
                                        "visible_text": visible_text,
                                    }
                                )

                                if len(results) >= max_results:
                                    return results

                        except Exception as e:
                            print(f"Error extracting result: {e}")

                except Exception as e:
                    print(f"Error fetching URL: {e}")

        return results


if __name__ == "__main__":
    from rich import print
    searcher = GoogleS()
    results = searcher.search("HelpingAI-9B", max_results=20, extract_webpage_text=True, max_extract_characters=200)
    for result in results:
        print(result)