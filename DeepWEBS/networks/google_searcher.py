import requests
from pathlib import Path
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

    def send_request(self, result_num=10, safe=False):
        self.request_response = requests.get(
            url=self.url,
            headers=REQUESTS_HEADERS,
            params={
                "q": self.query,
                "num": result_num,
            },
            proxies=self.enver.requests_proxies,
        )

    def save_response(self):
        if not self.html_path.exists():
            self.html_path.parent.mkdir(parents=True, exist_ok=True)
        logger.note(f"Saving to: [{self.html_path}]")
        with open(self.html_path, "wb") as wf:
            wf.write(self.request_response.content)

    def search(self, query, result_num=10, safe=False, overwrite=False):
        self.query = query
        self.html_path = self.filepath_converter.convert(self.query)
        logger.note(f"Searching: [{self.query}]")
        if self.html_path.exists() and not overwrite:
            logger.success(f"HTML existed: {self.html_path}")
        else:
            self.send_request(result_num=result_num, safe=safe)
            self.save_response()
        return self.html_path


if __name__ == "__main__":
    searcher = GoogleSearcher()
    searcher.search("python tutorials")
