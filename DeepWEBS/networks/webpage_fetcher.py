import concurrent.futures
import requests
import tldextract
from pathlib import Path
from DeepWEBS.utilsdw.enver import enver
from DeepWEBS.utilsdw.logger import logger
from DeepWEBS.networks.filepath_converter import UrlToFilepathConverter
from DeepWEBS.networks.network_configs import IGNORE_HOSTS, REQUESTS_HEADERS


class WebpageFetcher:
    def __init__(self):
        self.enver = enver
        self.enver.set_envs(proxies=True)
        self.filepath_converter = UrlToFilepathConverter()

    def is_ignored_host(self, url):
        self.host = tldextract.extract(url).registered_domain
        if self.host in IGNORE_HOSTS:
            return True
        else:
            return False

    def send_request(self):
        try:
            self.request_response = requests.get(
                url=self.url,
                headers=REQUESTS_HEADERS,
                proxies=self.enver.requests_proxies,
                timeout=15,
            )
        except:
            logger.warn(f"Failed to fetch: [{self.url}]")
            self.request_response = None

    def save_response(self):
        if not self.html_path.exists():
            self.html_path.parent.mkdir(parents=True, exist_ok=True)
        logger.success(f"Saving to: [{self.html_path}]")

        if self.request_response is None:
            return
        else:
            with open(self.html_path, "wb") as wf:
                wf.write(self.request_response.content)

    def fetch(self, url, overwrite=False, output_parent=None):
        self.url = url
        logger.note(f"Fetching: [{self.url}]")
        self.html_path = self.filepath_converter.convert(self.url, parent=output_parent)

        if self.is_ignored_host(self.url):
            logger.warn(f"Ignore host: [{self.host}]")
            return self.html_path

        if self.html_path.exists() and not overwrite:
            logger.success(f"HTML existed: [{self.html_path}]")
        else:
            self.send_request()
            self.save_response()
        return self.html_path


class BatchWebpageFetcher:
    def __init__(self):
        self.done_count = 0
        self.total_count = 0
        self.url_and_html_path_list = []

    def fecth_single_webpage(self, url, overwrite=False, output_parent=None):
        webpage_fetcher = WebpageFetcher()
        html_path = webpage_fetcher.fetch(
            url=url, overwrite=overwrite, output_parent=output_parent
        )
        self.url_and_html_path_list.append({"url": url, "html_path": html_path})
        self.done_count += 1
        logger.success(f"> [{self.done_count}/{self.total_count}] Fetched: {url}")

    def fetch(self, urls, overwrite=False, output_parent=None):
        self.urls = urls
        self.total_count = len(self.urls)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self.fecth_single_webpage,
                    url=url,
                    overwrite=overwrite,
                    output_parent=output_parent,
                )
                for url in urls
            ]

            for idx, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()
        return self.url_and_html_path_list


if __name__ == "__main__":
    urls = [
        "https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename",
        "https://www.liaoxuefeng.com/wiki/1016959663602400/1017495723838528",
        "https://docs.python.org/zh-cn/3/tutorial/interpreter.html",
    ]
    batch_webpage_fetcher = BatchWebpageFetcher()
    batch_webpage_fetcher.fetch(
        urls=urls, overwrite=True, output_parent="python tutorials"
    )
