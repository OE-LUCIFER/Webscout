import requests
from pathlib import Path
from typing import Optional
import random
from DeepWEBS.utilsdw.enver import enver
from DeepWEBS.utilsdw.logger import logger
from DeepWEBS.networks.filepath_converter import QueryToFilepathConverter
from DeepWEBS.networks.network_configs import REQUESTS_HEADERS

class GoogleSearcher:
    def __init__(self):
        self.url = "https://www.google.com/search"
        self.enver = enver
        self.enver.set_envs(proxies=True)
        self.filepath_converter = QueryToFilepathConverter()

    def send_request(self, query: str, result_num: int = 10, safe: bool = False) -> requests.Response:
        params = {
            "q": query,
            "num": result_num,
        }
        response = requests.get(
            self.url,
            headers=REQUESTS_HEADERS,
            params=params,
            proxies=self.enver.requests_proxies,
        )
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response

    def save_response(self, response: requests.Response, html_path: Path) -> None:
        html_path.parent.mkdir(parents=True, exist_ok=True)
        logger.note(f"Saving to: [{html_path}]")
        with html_path.open("wb") as wf:
            wf.write(response.content)

    def search(self, query: str, result_num: int = 10, safe: bool = False, overwrite: bool = False) -> Path:
        html_path = self.filepath_converter.convert(query)
        logger.note(f"Searching: [{query}]")

        if html_path.exists() and not overwrite:
            logger.success(f"HTML existed: {html_path}")
        else:
            response = self.send_request(query, result_num, safe)
            self.save_response(response, html_path)

        return html_path

if __name__ == "__main__":
    searcher = GoogleSearcher()
    html_path = searcher.search("python tutorials")
    print(f"HTML file saved at: {html_path}")