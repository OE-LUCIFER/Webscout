from __future__ import annotations

# import logging
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from functools import cached_property
from itertools import cycle, islice
from random import choice, shuffle
from threading import Event
from time import sleep, time
from types import TracebackType

import primp  # type: ignore

try:
    from lxml.etree import _Element
    from lxml.html import HTMLParser as LHTMLParser
    from lxml.html import document_fromstring

    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

from .exceptions import ConversationLimitException, WebscoutE, RatelimitE, TimeoutE
from .utils import (
    _calculate_distance,
    _expand_proxy_tb_alias,
    _extract_vqd,
    _normalize,
    _normalize_url,
    _text_extract_json,
    json_loads,
)

# logger = logging.getLogger("webscout.WEBS")


class WEBS:
    """webscout class to get search results from duckduckgo.com."""

    _executor: ThreadPoolExecutor = ThreadPoolExecutor()
    _impersonates = (
        "chrome_100", "chrome_101", "chrome_104", "chrome_105", "chrome_106", "chrome_107", "chrome_108", 
        "chrome_109", "chrome_114", "chrome_116", "chrome_117", "chrome_118", "chrome_119", "chrome_120", 
        #"chrome_123", "chrome_124", "chrome_126",
        "chrome_127", "chrome_128", "chrome_129",
        "safari_ios_16.5", "safari_ios_17.2", "safari_ios_17.4.1", "safari_15.3", "safari_15.5", "safari_15.6.1", 
        "safari_16", "safari_16.5", "safari_17.0", "safari_17.2.1", "safari_17.4.1", "safari_17.5", "safari_18", 
        "safari_ipad_18",
        "edge_101", "edge_122", "edge_127",
    )  # fmt: skip

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
        proxies: dict[str, str] | str | None = None,  # deprecated
        timeout: int | None = 10,
    ) -> None:
        """Initialize the WEBS object.

        Args:
            headers (dict, optional): Dictionary of headers for the HTTP client. Defaults to None.
            proxy (str, optional): proxy for the HTTP client, supports http/https/socks5 protocols.
                example: "http://user:pass@example.com:3128". Defaults to None.
            timeout (int, optional): Timeout value for the HTTP client. Defaults to 10.
        """
        self.proxy: str | None = _expand_proxy_tb_alias(proxy)
        assert self.proxy is None or isinstance(self.proxy, str), "proxy must be a str"
        if not proxy and proxies:
            warnings.warn("'proxies' is deprecated, use 'proxy' instead.", stacklevel=1)
            self.proxy = (
                proxies.get("http") or proxies.get("https")
                if isinstance(proxies, dict)
                else proxies
            )

        default_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Referer": "https://duckduckgo.com/",
        }

        self.headers = headers if headers else {}
        self.headers.update(default_headers)

        self.client = primp.Client(
            headers=self.headers,
            proxy=self.proxy,
            timeout=timeout,
            cookie_store=True,
            referer=True,
            impersonate=choice(self._impersonates),
            follow_redirects=True,
            verify=False,
        )
        self.sleep_timestamp = 0.0

        self._exception_event = Event()
        self._chat_messages: list[dict[str, str]] = []
        self._chat_tokens_count = 0
        self._chat_vqd: str = ""

    def __enter__(self) -> WEBS:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        pass

    @cached_property
    def parser(self) -> LHTMLParser:
        """Get HTML parser."""
        return LHTMLParser(
            remove_blank_text=True,
            remove_comments=True,
            remove_pis=True,
            collect_ids=False,
        )

    def _sleep(self, sleeptime: float = 2.0) -> None:
        """Sleep between API requests."""
        delay = (
            sleeptime
            if not self.sleep_timestamp
            else sleeptime
            if time() - self.sleep_timestamp >= 30
            else sleeptime * 2
        )
        self.sleep_timestamp = time()
        sleep(delay)

    def _get_url(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, str] | None = None,
    ) -> bytes:
        """Make HTTP request with proper rate limiting."""
        self._sleep()
        try:
            resp = self.client.request(
                method, url, params=params, content=content, data=data
            )

            # Add additional delay if we get a 429 or similar status
            if resp.status_code in (429, 403, 503):
                sleep(5.0)  # Additional delay for rate limit responses
                resp = self.client.request(
                    method, url, params=params, content=content, data=data
                )

        except Exception as ex:
            if "time" in str(ex).lower():
                raise TimeoutE(f"{url} {type(ex).__name__}: {ex}") from ex
            raise WebscoutE(f"{url} {type(ex).__name__}: {ex}") from ex

        if resp.status_code == 200:
            return resp.content
        elif resp.status_code in (202, 301, 403, 429, 503):
            raise RatelimitE(
                f"{url} {resp.status_code} Ratelimit - Please wait a few minutes before retrying"
            )
        raise WebscoutE(f"{url} return None. {params=} {content=} {data=}")

    def _get_vqd(self, keywords: str) -> str:
        """Get vqd value for a search query."""
        resp_content = self._get_url(
            "GET", "https://duckduckgo.com", params={"q": keywords}
        )
        return _extract_vqd(resp_content, keywords)

    def chat(self, keywords: str, model: str = "gpt-4o-mini", timeout: int = 30) -> str:
        """Initiates a chat session with webscout AI.

        Args:
            keywords (str): The initial message or question to send to the AI.
            model (str): The model to use: "gpt-4o-mini", "claude-3-haiku", "llama-3.1-70b", "mixtral-8x7b".
                Defaults to "gpt-4o-mini".
            timeout (int): Timeout value for the HTTP client. Defaults to 20.

        Returns:
            str: The response from the AI.
        """
        models_deprecated = {"gpt-3.5": "gpt-4o-mini", "llama-3-70b": "llama-3.1-70b"}
        if model in models_deprecated:
            # logger.info(f"{model=} is deprecated, using {models_deprecated[model]}")
            model = models_deprecated[model]
        models = {
            "claude-3-haiku": "claude-3-haiku-20240307",
            "gpt-4o-mini": "gpt-4o-mini",
            "llama-3.1-70b": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "o3-mini": "o3-mini",
        }
        # vqd
        if not self._chat_vqd:
            resp = self.client.get(
                "https://duckduckgo.com/duckchat/v1/status",
                headers={"x-vqd-accept": "1"},
            )
            self._chat_vqd = resp.headers.get("x-vqd-4", "")

        self._chat_messages.append({"role": "user", "content": keywords})
        self._chat_tokens_count += (
            len(keywords) // 4 if len(keywords) >= 4 else 1
        )  # approximate number of tokens

        json_data = {
            "model": models[model],
            "messages": self._chat_messages,
        }
        resp = self.client.post(
            "https://duckduckgo.com/duckchat/v1/chat",
            headers={"x-vqd-4": self._chat_vqd},
            json=json_data,
            timeout=timeout,
        )
        self._chat_vqd = resp.headers.get("x-vqd-4", "")

        data = ",".join(
            line.strip()
            for line in resp.text.rstrip("[DONE]LIMT_CVRSA\n").split("data:")
            if line.strip()
        )
        data = json_loads("[" + data + "]")

        results = []
        for x in data:
            if x.get("action") == "error":
                err_message = x.get("type", "")
                if x.get("status") == 429:
                    raise (
                        ConversationLimitException(err_message)
                        if err_message == "ERR_CONVERSATION_LIMIT"
                        else RatelimitE(err_message)
                    )
                raise WebscoutE(err_message)
            elif message := x.get("message"):
                results.append(message)
        result = "".join(results)

        self._chat_messages.append({"role": "assistant", "content": result})
        self._chat_tokens_count += len(results)
        return result

    def text(
        self,
        keywords: str,
        region: str = "wt-wt",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        backend: str = "auto",
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """webscout text search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".
            safesearch: on, moderate, off. Defaults to "moderate".
            timelimit: d, w, m, y. Defaults to None.
            backend: auto, html, lite. Defaults to auto.
                auto - try all backends in random order,
                html - collect data from https://html.duckduckgo.com,
                lite - collect data from https://lite.duckduckgo.com.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with search results.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        if backend in ("api", "ecosia"):
            warnings.warn(
                f"{backend=} is deprecated, using backend='auto'", stacklevel=2
            )
            backend = "auto"
        backends = ["html", "lite"] if backend == "auto" else [backend]
        shuffle(backends)

        results, err = [], None
        for b in backends:
            try:
                if b == "html":
                    results = self._text_html(keywords, region, timelimit, max_results)
                elif b == "lite":
                    results = self._text_lite(keywords, region, timelimit, max_results)
                return results
            except Exception as ex:
                err = ex

        raise WebscoutE(err)

    def _text_api(
        self,
        keywords: str,
        region: str = "wt-wt",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """webscout text search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".
            safesearch: on, moderate, off. Defaults to "moderate".
            timelimit: d, w, m, y. Defaults to None.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with search results.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        vqd = self._get_vqd(keywords)

        payload = {
            "q": keywords,
            "kl": region,
            "l": region,
            "p": "",
            "s": "0",
            "df": "",
            "vqd": vqd,
            "bing_market": f"{region[3:]}-{region[:2].upper()}",
            "ex": "",
        }
        safesearch = safesearch.lower()
        if safesearch == "moderate":
            payload["ex"] = "-1"
        elif safesearch == "off":
            payload["ex"] = "-2"
        elif safesearch == "on":  # strict
            payload["p"] = "1"
        if timelimit:
            payload["df"] = timelimit

        cache = set()
        results: list[dict[str, str]] = []

        def _text_api_page(s: int) -> list[dict[str, str]]:
            payload["s"] = f"{s}"
            resp_content = self._get_url(
                "GET", "https://links.duckduckgo.com/d.js", params=payload
            )
            page_data = _text_extract_json(resp_content, keywords)
            page_results = []
            for row in page_data:
                href = row.get("u", None)
                if (
                    href
                    and href not in cache
                    and href != f"http://www.google.com/search?q={keywords}"
                ):
                    cache.add(href)
                    body = _normalize(row["a"])
                    if body:
                        result = {
                            "title": _normalize(row["t"]),
                            "href": _normalize_url(href),
                            "body": body,
                        }
                        page_results.append(result)
            return page_results

        slist = [0]
        if max_results:
            max_results = min(max_results, 2023)
            slist.extend(range(23, max_results, 50))
        try:
            for r in self._executor.map(_text_api_page, slist):
                results.extend(r)
        except Exception as e:
            raise e

        return list(islice(results, max_results))

    def _text_html(
        self,
        keywords: str,
        region: str = "wt-wt",
        timelimit: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """webscout text search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".
            timelimit: d, w, m, y. Defaults to None.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with search results.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        payload = {
            "q": keywords,
            "s": "0",
            "o": "json",
            "api": "d.js",
            "vqd": "",
            "kl": region,
            "bing_market": region,
        }
        if timelimit:
            payload["df"] = timelimit
        if max_results and max_results > 20:
            vqd = self._get_vqd(keywords)
            payload["vqd"] = vqd

        cache = set()
        results: list[dict[str, str]] = []

        def _text_html_page(s: int) -> list[dict[str, str]]:
            payload["s"] = f"{s}"
            resp_content = self._get_url(
                "POST", "https://html.duckduckgo.com/html", data=payload
            )
            if b"No  results." in resp_content:
                return []

            page_results = []
            tree = document_fromstring(resp_content, self.parser)
            elements = tree.xpath("//div[h2]")
            if not isinstance(elements, list):
                return []
            for e in elements:
                if isinstance(e, _Element):
                    hrefxpath = e.xpath("./a/@href")
                    href = (
                        str(hrefxpath[0])
                        if hrefxpath and isinstance(hrefxpath, list)
                        else None
                    )
                    if (
                        href
                        and href not in cache
                        and not href.startswith(
                            (
                                "http://www.google.com/search?q=",
                                "https://duckduckgo.com/y.js?ad_domain",
                            )
                        )
                    ):
                        cache.add(href)
                        titlexpath = e.xpath("./h2/a/text()")
                        title = (
                            str(titlexpath[0])
                            if titlexpath and isinstance(titlexpath, list)
                            else ""
                        )
                        bodyxpath = e.xpath("./a//text()")
                        body = (
                            "".join(str(x) for x in bodyxpath)
                            if bodyxpath and isinstance(bodyxpath, list)
                            else ""
                        )
                        result = {
                            "title": _normalize(title),
                            "href": _normalize_url(href),
                            "body": _normalize(body),
                        }
                        page_results.append(result)
            return page_results

        slist = [0]
        if max_results:
            max_results = min(max_results, 2023)
            slist.extend(range(23, max_results, 50))
        try:
            for r in self._executor.map(_text_html_page, slist):
                results.extend(r)
        except Exception as e:
            raise e

        return list(islice(results, max_results))

    def _text_lite(
        self,
        keywords: str,
        region: str = "wt-wt",
        timelimit: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """webscout text search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".
            timelimit: d, w, m, y. Defaults to None.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with search results.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        payload = {
            "q": keywords,
            "s": "0",
            "o": "json",
            "api": "d.js",
            "vqd": "",
            "kl": region,
            "bing_market": region,
        }
        if timelimit:
            payload["df"] = timelimit

        cache = set()
        results: list[dict[str, str]] = []

        def _text_lite_page(s: int) -> list[dict[str, str]]:
            payload["s"] = f"{s}"
            resp_content = self._get_url(
                "POST", "https://lite.duckduckgo.com/lite/", data=payload
            )
            if b"No more results." in resp_content:
                return []

            page_results = []
            tree = document_fromstring(resp_content, self.parser)
            elements = tree.xpath("//table[last()]//tr")
            if not isinstance(elements, list):
                return []

            data = zip(cycle(range(1, 5)), elements)
            for i, e in data:
                if isinstance(e, _Element):
                    if i == 1:
                        hrefxpath = e.xpath(".//a//@href")
                        href = (
                            str(hrefxpath[0])
                            if hrefxpath and isinstance(hrefxpath, list)
                            else None
                        )
                        if (
                            href is None
                            or href in cache
                            or href.startswith(
                                (
                                    "http://www.google.com/search?q=",
                                    "https://duckduckgo.com/y.js?ad_domain",
                                )
                            )
                        ):
                            [
                                next(data, None) for _ in range(3)
                            ]  # skip block(i=1,2,3,4)
                        else:
                            cache.add(href)
                            titlexpath = e.xpath(".//a//text()")
                            title = (
                                str(titlexpath[0])
                                if titlexpath and isinstance(titlexpath, list)
                                else ""
                            )
                    elif i == 2:
                        bodyxpath = e.xpath(".//td[@class='result-snippet']//text()")
                        body = (
                            "".join(str(x) for x in bodyxpath).strip()
                            if bodyxpath and isinstance(bodyxpath, list)
                            else ""
                        )
                        if href:
                            result = {
                                "title": _normalize(title),
                                "href": _normalize_url(href),
                                "body": _normalize(body),
                            }
                            page_results.append(result)
            return page_results

        slist = [0]
        if max_results:
            max_results = min(max_results, 2023)
            slist.extend(range(23, max_results, 50))
        try:
            for r in self._executor.map(_text_lite_page, slist):
                results.extend(r)
        except Exception as e:
            raise e

        return list(islice(results, max_results))

    def images(
        self,
        keywords: str,
        region: str = "wt-wt",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        size: str | None = None,
        color: str | None = None,
        type_image: str | None = None,
        layout: str | None = None,
        license_image: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """webscout images search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".
            safesearch: on, moderate, off. Defaults to "moderate".
            timelimit: Day, Week, Month, Year. Defaults to None.
            size: Small, Medium, Large, Wallpaper. Defaults to None.
            color: color, Monochrome, Red, Orange, Yellow, Green, Blue,
                Purple, Pink, Brown, Black, Gray, Teal, White. Defaults to None.
            type_image: photo, clipart, gif, transparent, line.
                Defaults to None.
            layout: Square, Tall, Wide. Defaults to None.
            license_image: any (All Creative Commons), Public (PublicDomain),
                Share (Free to Share and Use), ShareCommercially (Free to Share and Use Commercially),
                Modify (Free to Modify, Share, and Use), ModifyCommercially (Free to Modify, Share, and
                Use Commercially). Defaults to None.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with images search results.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        vqd = self._get_vqd(keywords)

        safesearch_base = {"on": "1", "moderate": "1", "off": "-1"}
        timelimit = f"time:{timelimit}" if timelimit else ""
        size = f"size:{size}" if size else ""
        color = f"color:{color}" if color else ""
        type_image = f"type:{type_image}" if type_image else ""
        layout = f"layout:{layout}" if layout else ""
        license_image = f"license:{license_image}" if license_image else ""
        payload = {
            "l": region,
            "o": "json",
            "q": keywords,
            "vqd": vqd,
            "f": f"{timelimit},{size},{color},{type_image},{layout},{license_image}",
            "p": safesearch_base[safesearch.lower()],
        }

        cache = set()
        results: list[dict[str, str]] = []

        def _images_page(s: int) -> list[dict[str, str]]:
            payload["s"] = f"{s}"
            resp_content = self._get_url(
                "GET", "https://duckduckgo.com/i.js", params=payload
            )
            resp_json = json_loads(resp_content)

            page_data = resp_json.get("results", [])
            page_results = []
            for row in page_data:
                image_url = row.get("image")
                if image_url and image_url not in cache:
                    cache.add(image_url)
                    result = {
                        "title": row["title"],
                        "image": _normalize_url(image_url),
                        "thumbnail": _normalize_url(row["thumbnail"]),
                        "url": _normalize_url(row["url"]),
                        "height": row["height"],
                        "width": row["width"],
                        "source": row["source"],
                    }
                    page_results.append(result)
            return page_results

        slist = [0]
        if max_results:
            max_results = min(max_results, 500)
            slist.extend(range(100, max_results, 100))
        try:
            for r in self._executor.map(_images_page, slist):
                results.extend(r)
        except Exception as e:
            raise e

        return list(islice(results, max_results))

    def videos(
        self,
        keywords: str,
        region: str = "wt-wt",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        resolution: str | None = None,
        duration: str | None = None,
        license_videos: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """webscout videos search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".
            safesearch: on, moderate, off. Defaults to "moderate".
            timelimit: d, w, m. Defaults to None.
            resolution: high, standart. Defaults to None.
            duration: short, medium, long. Defaults to None.
            license_videos: creativeCommon, youtube. Defaults to None.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with videos search results.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        vqd = self._get_vqd(keywords)

        safesearch_base = {"on": "1", "moderate": "-1", "off": "-2"}
        timelimit = f"publishedAfter:{timelimit}" if timelimit else ""
        resolution = f"videoDefinition:{resolution}" if resolution else ""
        duration = f"videoDuration:{duration}" if duration else ""
        license_videos = f"videoLicense:{license_videos}" if license_videos else ""
        payload = {
            "l": region,
            "o": "json",
            "q": keywords,
            "vqd": vqd,
            "f": f"{timelimit},{resolution},{duration},{license_videos}",
            "p": safesearch_base[safesearch.lower()],
        }

        cache = set()
        results: list[dict[str, str]] = []

        def _videos_page(s: int) -> list[dict[str, str]]:
            payload["s"] = f"{s}"
            resp_content = self._get_url(
                "GET", "https://duckduckgo.com/v.js", params=payload
            )
            resp_json = json_loads(resp_content)

            page_data = resp_json.get("results", [])
            page_results = []
            for row in page_data:
                if row["content"] not in cache:
                    cache.add(row["content"])
                    page_results.append(row)
            return page_results

        slist = [0]
        if max_results:
            max_results = min(max_results, 400)
            slist.extend(range(60, max_results, 60))
        try:
            for r in self._executor.map(_videos_page, slist):
                results.extend(r)
        except Exception as e:
            raise e

        return list(islice(results, max_results))

    def news(
        self,
        keywords: str,
        region: str = "wt-wt",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """webscout news search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".
            safesearch: on, moderate, off. Defaults to "moderate".
            timelimit: d, w, m. Defaults to None.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with news search results.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        vqd = self._get_vqd(keywords)

        safesearch_base = {"on": "1", "moderate": "-1", "off": "-2"}
        payload = {
            "l": region,
            "o": "json",
            "noamp": "1",
            "q": keywords,
            "vqd": vqd,
            "p": safesearch_base[safesearch.lower()],
        }
        if timelimit:
            payload["df"] = timelimit

        cache = set()
        results: list[dict[str, str]] = []

        def _news_page(s: int) -> list[dict[str, str]]:
            payload["s"] = f"{s}"
            resp_content = self._get_url(
                "GET", "https://duckduckgo.com/news.js", params=payload
            )
            resp_json = json_loads(resp_content)
            page_data = resp_json.get("results", [])
            page_results = []
            for row in page_data:
                if row["url"] not in cache:
                    cache.add(row["url"])
                    image_url = row.get("image", None)
                    result = {
                        "date": datetime.fromtimestamp(
                            row["date"], timezone.utc
                        ).isoformat(),
                        "title": row["title"],
                        "body": _normalize(row["excerpt"]),
                        "url": _normalize_url(row["url"]),
                        "image": _normalize_url(image_url),
                        "source": row["source"],
                    }
                    page_results.append(result)
            return page_results

        slist = [0]
        if max_results:
            max_results = min(max_results, 120)
            slist.extend(range(30, max_results, 30))
        try:
            for r in self._executor.map(_news_page, slist):
                results.extend(r)
        except Exception as e:
            raise e

        return list(islice(results, max_results))

    def answers(self, keywords: str) -> list[dict[str, str]]:
        """webscout instant answers. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query,

        Returns:
            List of dictionaries with instant answers results.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        payload = {
            "q": f"what is {keywords}",
            "format": "json",
        }
        resp_content = self._get_url(
            "GET", "https://api.duckduckgo.com/", params=payload
        )
        page_data = json_loads(resp_content)

        results = []
        answer = page_data.get("AbstractText")
        url = page_data.get("AbstractURL")
        if answer:
            results.append(
                {
                    "icon": None,
                    "text": answer,
                    "topic": None,
                    "url": url,
                }
            )

        # related
        payload = {
            "q": f"{keywords}",
            "format": "json",
        }
        resp_content = self._get_url(
            "GET", "https://api.duckduckgo.com/", params=payload
        )
        resp_json = json_loads(resp_content)
        page_data = resp_json.get("RelatedTopics", [])

        for row in page_data:
            topic = row.get("Name")
            if not topic:
                icon = row["Icon"].get("URL")
                results.append(
                    {
                        "icon": f"https://duckduckgo.com{icon}" if icon else "",
                        "text": row["Text"],
                        "topic": None,
                        "url": row["FirstURL"],
                    }
                )
            else:
                for subrow in row["Topics"]:
                    icon = subrow["Icon"].get("URL")
                    results.append(
                        {
                            "icon": f"https://duckduckgo.com{icon}" if icon else "",
                            "text": subrow["Text"],
                            "topic": topic,
                            "url": subrow["FirstURL"],
                        }
                    )

        return results

    def suggestions(self, keywords: str, region: str = "wt-wt") -> list[dict[str, str]]:
        """webscout suggestions. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".

        Returns:
            List of dictionaries with suggestions results.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        payload = {
            "q": keywords,
            "kl": region,
        }
        resp_content = self._get_url(
            "GET", "https://duckduckgo.com/ac/", params=payload
        )
        page_data = json_loads(resp_content)
        return [r for r in page_data]

    def maps(
        self,
        keywords: str,
        place: str | None = None,
        street: str | None = None,
        city: str | None = None,
        county: str | None = None,
        state: str | None = None,
        country: str | None = None,
        postalcode: str | None = None,
        latitude: str | None = None,
        longitude: str | None = None,
        radius: int = 0,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """webscout maps search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query
            place: if set, the other parameters are not used. Defaults to None.
            street: house number/street. Defaults to None.
            city: city of search. Defaults to None.
            county: county of search. Defaults to None.
            state: state of search. Defaults to None.
            country: country of search. Defaults to None.
            postalcode: postalcode of search. Defaults to None.
            latitude: geographic coordinate (north-south position). Defaults to None.
            longitude: geographic coordinate (east-west position); if latitude and
                longitude are set, the other parameters are not used. Defaults to None.
            radius: expand the search square by the distance in kilometers. Defaults to 0.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with maps search results, or None if there was an error.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        vqd = self._get_vqd(keywords)

        # if longitude and latitude are specified, skip the request about bbox to the nominatim api
        if latitude and longitude:
            lat_t = Decimal(latitude.replace(",", "."))
            lat_b = Decimal(latitude.replace(",", "."))
            lon_l = Decimal(longitude.replace(",", "."))
            lon_r = Decimal(longitude.replace(",", "."))
            if radius == 0:
                radius = 1
        # otherwise request about bbox to nominatim api
        else:
            if place:
                params = {
                    "q": place,
                    "polygon_geojson": "0",
                    "format": "jsonv2",
                }
            else:
                params = {
                    "polygon_geojson": "0",
                    "format": "jsonv2",
                }
                if street:
                    params["street"] = street
                if city:
                    params["city"] = city
                if county:
                    params["county"] = county
                if state:
                    params["state"] = state
                if country:
                    params["country"] = country
                if postalcode:
                    params["postalcode"] = postalcode
            # request nominatim api to get coordinates box
            resp_content = self._get_url(
                "GET",
                "https://nominatim.openstreetmap.org/search.php",
                params=params,
            )
            if resp_content == b"[]":
                raise WebscoutE(
                    "maps() Coordinates are not found, check function parameters."
                )
            resp_json = json_loads(resp_content)
            coordinates = resp_json[0]["boundingbox"]
            lat_t, lon_l = Decimal(coordinates[1]), Decimal(coordinates[2])
            lat_b, lon_r = Decimal(coordinates[0]), Decimal(coordinates[3])

        # if a radius is specified, expand the search square
        lat_t += Decimal(radius) * Decimal(0.008983)
        lat_b -= Decimal(radius) * Decimal(0.008983)
        lon_l -= Decimal(radius) * Decimal(0.008983)
        lon_r += Decimal(radius) * Decimal(0.008983)
        # logger.debug(f"bbox coordinates\n{lat_t} {lon_l}\n{lat_b} {lon_r}")

        cache = set()
        results: list[dict[str, str]] = []

        def _maps_page(
            bbox: tuple[Decimal, Decimal, Decimal, Decimal],
        ) -> list[dict[str, str]] | None:
            if max_results and len(results) >= max_results:
                return None
            lat_t, lon_l, lat_b, lon_r = bbox
            params = {
                "q": keywords,
                "vqd": vqd,
                "tg": "maps_places",
                "rt": "D",
                "mkexp": "b",
                "wiki_info": "1",
                "is_requery": "1",
                "bbox_tl": f"{lat_t},{lon_l}",
                "bbox_br": f"{lat_b},{lon_r}",
                "strict_bbox": "1",
            }
            resp_content = self._get_url(
                "GET", "https://duckduckgo.com/local.js", params=params
            )
            resp_json = json_loads(resp_content)
            page_data = resp_json.get("results", [])

            page_results = []
            for res in page_data:
                r_name = f"{res['name']} {res['address']}"
                if r_name in cache:
                    continue
                else:
                    cache.add(r_name)
                    result = {
                        "title": res["name"],
                        "address": res["address"],
                        "country_code": res["country_code"],
                        "url": _normalize_url(res["website"]),
                        "phone": res["phone"] or "",
                        "latitude": res["coordinates"]["latitude"],
                        "longitude": res["coordinates"]["longitude"],
                        "source": _normalize_url(res["url"]),
                        "image": x.get("image", "") if (x := res["embed"]) else "",
                        "desc": x.get("description", "") if (x := res["embed"]) else "",
                        "hours": res["hours"] or "",
                        "category": res["ddg_category"] or "",
                        "facebook": f"www.facebook.com/profile.php?id={x}"
                        if (x := res["facebook_id"])
                        else "",
                        "instagram": f"https://www.instagram.com/{x}"
                        if (x := res["instagram_id"])
                        else "",
                        "twitter": f"https://twitter.com/{x}"
                        if (x := res["twitter_id"])
                        else "",
                    }
                    page_results.append(result)
            return page_results

        # search squares (bboxes)
        start_bbox = (lat_t, lon_l, lat_b, lon_r)
        work_bboxes = [start_bbox]
        while work_bboxes:
            queue_bboxes = []  # for next iteration, at the end of the iteration work_bboxes = queue_bboxes
            tasks = []
            for bbox in work_bboxes:
                tasks.append(bbox)
                # if distance between coordinates > 1, divide the square into 4 parts and save them in queue_bboxes
                if _calculate_distance(lat_t, lon_l, lat_b, lon_r) > 1:
                    lat_t, lon_l, lat_b, lon_r = bbox
                    lat_middle = (lat_t + lat_b) / 2
                    lon_middle = (lon_l + lon_r) / 2
                    bbox1 = (lat_t, lon_l, lat_middle, lon_middle)
                    bbox2 = (lat_t, lon_middle, lat_middle, lon_r)
                    bbox3 = (lat_middle, lon_l, lat_b, lon_middle)
                    bbox4 = (lat_middle, lon_middle, lat_b, lon_r)
                    queue_bboxes.extend([bbox1, bbox2, bbox3, bbox4])

            # gather tasks using asyncio.wait_for and timeout
            work_bboxes_results = []
            try:
                for r in self._executor.map(_maps_page, tasks):
                    if r:
                        work_bboxes_results.extend(r)
            except Exception as e:
                raise e

            for x in work_bboxes_results:
                if isinstance(x, list):
                    results.extend(x)
                elif isinstance(x, dict):
                    results.append(x)

            work_bboxes = queue_bboxes
            if (
                not max_results
                or len(results) >= max_results
                or len(work_bboxes_results) == 0
            ):
                break

        return list(islice(results, max_results))

    def translate(
        self, keywords: list[str] | str, from_: str | None = None, to: str = "en"
    ) -> list[dict[str, str]]:
        """webscout translate.

        Args:
            keywords: string or list of strings to translate.
            from_: translate from (defaults automatically). Defaults to None.
            to: what language to translate. Defaults to "en".

        Returns:
            List od dictionaries with translated keywords.

        Raises:
            WebscoutE: Base exception for webscout errors.
            RatelimitE: Inherits from WebscoutE, raised for exceeding API request rate limits.
            TimeoutE: Inherits from WebscoutE, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        vqd = self._get_vqd("translate")

        payload = {
            "vqd": vqd,
            "query": "translate",
            "to": to,
        }
        if from_:
            payload["from"] = from_

        def _translate_keyword(keyword: str) -> dict[str, str]:
            resp_content = self._get_url(
                "POST",
                "https://duckduckgo.com/translation.js",
                params=payload,
                content=keyword.encode(),
            )
            page_data: dict[str, str] = json_loads(resp_content)
            page_data["original"] = keyword
            return page_data

        if isinstance(keywords, str):
            keywords = [keywords]

        results = []
        try:
            for r in self._executor.map(_translate_keyword, keywords):
                results.append(r)
        except Exception as e:
            raise e

        return results
