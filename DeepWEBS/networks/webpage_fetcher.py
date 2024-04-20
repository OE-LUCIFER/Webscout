import concurrent.futures
import random
import requests
import tldextract
from pathlib import Path
from typing import List, Tuple, Dict

from DeepWEBS.utilsdw.enver import enver
from DeepWEBS.utilsdw.logger import logger
from DeepWEBS.networks.filepath_converter import UrlToFilepathConverter
from DeepWEBS.networks.network_configs import IGNORE_HOSTS, REQUESTS_HEADERS

class WebpageFetcher:
    def __init__(self):
        self.enver = enver
        self.enver.set_envs(proxies=True)
        self.filepath_converter = UrlToFilepathConverter()

    def is_ignored_host(self, url: str) -> bool:
        host = tldextract.extract(url).registered_domain
        return host in IGNORE_HOSTS

    def send_request(self, url: str) -> requests.Response:
        try:
            user_agent = random.choice(REQUESTS_HEADERS["User-Agent"])
            response = requests.get(
                url=url,
                headers={"User-Agent": user_agent},
                proxies=self.enver.requests_proxies,
                timeout=15,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warn(f"Failed to fetch: [{url}] | {e}")
            return None

    def save_response(self, response: requests.Response, html_path: Path) -> None:
        if response is None:
            return

        html_path.parent.mkdir(parents=True, exist_ok=True)
        logger.success(f"Saving to: [{html_path}]")
        with html_path.open("wb") as wf:
            wf.write(response.content)

    def fetch(self, url: str, overwrite: bool = False, output_parent: str = None) -> Path:
        logger.note(f"Fetching: [{url}]")
        html_path = self.filepath_converter.convert(url, parent=output_parent)

        if self.is_ignored_host(url):
            logger.warn(f"Ignored host: [{tldextract.extract(url).registered_domain}]")
            return html_path

        if html_path.exists() and not overwrite:
            logger.success(f"HTML existed: [{html_path}]")
        else:
            response = self.send_request(url)
            self.save_response(response, html_path)

        return html_path

class BatchWebpageFetcher:
    def __init__(self):
        self.done_count = 0
        self.total_count = 0
        self.url_and_html_path_list: List[Dict[str, str]] = []

    def fetch_single_webpage(self, url: str, overwrite: bool = False, output_parent: str = None) -> Tuple[str, Path]:
        webpage_fetcher = WebpageFetcher()
        html_path = webpage_fetcher.fetch(url, overwrite, output_parent)
        self.url_and_html_path_list.append({"url": url, "html_path": str(html_path)})
        self.done_count += 1
        logger.success(f"> [{self.done_count}/{self.total_count}] Fetched: {url}")
        return url, html_path

    def fetch(self, urls: List[str], overwrite: bool = False, output_parent: str = None) -> List[Dict[str, str]]:
        self.urls = urls
        self.total_count = len(self.urls)

        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(WebpageFetcher().fetch, url, overwrite, output_parent)
                for url in urls
            ]
            concurrent.futures.wait(futures)

        self.url_and_html_path_list = [
            {"url": future.result().url, "html_path": str(future.result().html_path)}
            for future in futures
        ]

        return self.url_and_html_path_list


