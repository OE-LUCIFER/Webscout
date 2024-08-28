from bs4 import BeautifulSoup
import requests
from typing import Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from termcolor import colored
import time
import random

class GoogleS:
    """
    Class to perform Google searches and retrieve results.
    """

    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = 10,
        max_workers: int = 20  # Increased max workers for thread pool
    ):
        """Initializes the GoogleS object."""
        self.proxy = proxy
        self.headers = headers if headers else {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62"
        }
        self.headers["Referer"] = "https://www.google.com/"
        self.client = requests.Session()
        self.client.headers.update(self.headers)
        self.client.proxies.update({"http": self.proxy, "https": self.proxy})
        self.timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=max_workers) 

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def _get_url(self, method: str, url: str, params: Optional[Dict[str, str]] = None,
                  data: Optional[Union[Dict[str, str], bytes]] = None) -> bytes:
        """
        Makes an HTTP request and returns the response content.
        """
        try:
            resp = self.client.request(method, url, params=params, data=data, timeout=self.timeout)
        except Exception as ex:
            raise Exception(f"{url} {type(ex).__name__}: {ex}") from ex
        if resp.status_code == 200:
            return resp.content
        raise Exception(f"{resp.url} returned status code {resp.status_code}. {params=} {data=}")

    def _extract_text_from_webpage(self, html_content: bytes, max_characters: Optional[int] = None) -> str:
        """
        Extracts visible text from HTML content using lxml parser.
        """
        soup = BeautifulSoup(html_content, 'lxml')  # Use lxml parser
        for tag in soup(["script", "style", "header", "footer", "nav"]):
            tag.extract()
        visible_text = soup.get_text(strip=True)
        if max_characters:
            visible_text = visible_text[:max_characters]
        return visible_text

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
    ) -> List[Dict[str, Union[str, int]]]:
        """
        Performs a Google search and returns the results.

        Args:
            query (str): The search query.
            region (str, optional): The region to search in (e.g., "us-en"). Defaults to "us-en".
            language (str, optional): The language of the search results (e.g., "en"). Defaults to "en".
            safe (str, optional): Safe search setting ("off", "active"). Defaults to "off".
            time_period (Optional[str], optional): Time period filter (e.g., "h" for past hour, "d" for past day). 
                                                   Defaults to None.
            max_results (int, optional): The maximum number of results to retrieve. Defaults to 10.
            extract_text (bool, optional): Whether to extract text from the linked web pages. Defaults to False.
            max_text_length (Optional[int], optional): The maximum length of the extracted text (in characters). 
                                                      Defaults to 100.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries, each representing a search result, containing:
                - 'title': The title of the result.
                - 'href': The URL of the result.
                - 'abstract': The description snippet of the result.
                - 'index': The index of the result in the list.
                - 'type': The type of result (currently always "web").
                - 'visible_text': The extracted text from the web page (if `extract_text` is True).
        """
        assert query, "Query cannot be empty."

        results = []
        futures = []
        start = 0

        while len(results) < max_results:
            params = {
                "q": query,
                "num": 10,
                "hl": language,
                "start": start,
                "safe": safe,
                "gl": region,
            }
            if time_period:
                params["tbs"] = f"qdr:{time_period}"

            futures.append(self._executor.submit(self._get_url, "GET", "https://www.google.com/search", params=params))
            start += 10

            for future in as_completed(futures):
                try:
                    resp_content = future.result()
                    soup = BeautifulSoup(resp_content, 'lxml')  # Use lxml parser
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

        return results


if __name__ == "__main__":
    from rich import print
    searcher = GoogleS()
    results = searcher.search("HelpingAI-9B", max_results=20, extract_text=False, max_text_length=200)
    for result in results:
        print(result)