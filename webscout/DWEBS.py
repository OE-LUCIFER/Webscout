from bs4 import BeautifulSoup
from pathlib import Path
import platform
import re
import concurrent.futures
import requests
import tldextract
import json
import os
import shutil
import subprocess
import datetime
import functools
import inspect
import logging

from urllib.parse import quote, unquote
from tiktoken import get_encoding as tiktoken_get_encoding
from markdownify import markdownify
from termcolor import colored
class QueryResultsExtractor:
    def __init__(self) -> None:
        self.query_results = []
        self.related_questions = []

    def load_html(self, html_path):
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            self.soup = BeautifulSoup(html, "html.parser")
        except FileNotFoundError:
            logger.error(f"File not found: {html_path}")
        except Exception as e:
            logger.error(f"Error loading HTML: {e}")

    def extract_query_results(self):
        try:
            self.query = self.soup.find("textarea").text.strip()
            query_result_elements = self.soup.find_all("div", class_="g")
            for idx, result in enumerate(query_result_elements):
                try:
                    site = result.find("cite").find_previous("span").text.strip()
                    url = result.find("a")["href"]
                    title = result.find("h3").text.strip()
                    abstract_element_conditions = [
                        {"data-sncf": "1"},
                        {"class_": "ITZIwc"},
                    ]
                    for condition in abstract_element_conditions:
                        abstract_element = result.find("div", condition)
                        if abstract_element is not None:
                            abstract = abstract_element.text.strip()
                            break
                    else:
                        abstract = ""
                    logger.mesg(
                        f"{title}\n"
                        f" - {site}\n"
                        f" - {url}\n"
                        f" - {abstract}\n"
                        f"\n"
                    )
                    self.query_results.append(
                        {
                            "title": title,
                            "site": site,
                            "url": url,
                            "abstract": abstract,
                            "index": idx,
                            "type": "web",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error extracting query result: {e}")
            logger.success(f"- {len(query_result_elements)} query results")
        except Exception as e:
            logger.error(f"Error extracting query results: {e}")

    def extract_related_questions(self):
        try:
            related_question_elements = self.soup.find_all(
                "div", class_="related-question-pair"
            )
            for question_element in related_question_elements:
                try:
                    question = question_element.find("span").text.strip()
                    print(question)
                    self.related_questions.append(question)
                except Exception as e:
                    logger.error(f"Error extracting related question: {e}")
            logger.success(f"- {len(self.related_questions)} related questions")
        except Exception as e:
            logger.error(f"Error extracting related questions: {e}")

    def extract(self, html_path):
        self.load_html(html_path)
        self.extract_query_results()
        self.extract_related_questions()
        self.search_results = {
            "query": self.query,
            "query_results": self.query_results,
            "related_questions": self.related_questions,
        }
        return self.search_results




class WebpageContentExtractor:
    def __init__(self):
        self.tokenizer = tiktoken_get_encoding("cl100k_base")

    def count_tokens(self, text):
        tokens = self.tokenizer.encode(text)
        token_count = len(tokens)
        return token_count

    def html_to_markdown(self, html_str, ignore_links=True):
        if ignore_links:
            markdown_str = markdownify(html_str, strip="a")
        else:
            markdown_str = markdownify(html_str)
        markdown_str = re.sub(r"\n{3,}", "\n\n", markdown_str)

        self.markdown_token_count = self.count_tokens(markdown_str)
        logger.mesg(f'- Tokens: {colored(self.markdown_token_count,"light_green")}')

        self.markdown_str = markdown_str

        return self.markdown_str

    def remove_elements_from_html(self, html_str):
        soup = BeautifulSoup(html_str, "html.parser")
        ignore_classes_with_parentheses = [f"({word})" for word in IGNORE_CLASSES]
        ignore_classes_pattern = f'{"|".join(ignore_classes_with_parentheses)}'
        removed_element_counts = 0
        for element in soup.find_all():
            class_str = ""
            id_str = ""
            try:
                class_attr = element.get("class", [])
                if class_attr:
                    class_str = " ".join(list(class_attr))
                if id_str:
                    class_str = f"{class_str} {id_str}"
            except:
                pass

            try:
                id_str = element.get("id", "")
            except:
                pass

            if (
                (not element.text.strip())
                or (element.name in IGNORE_TAGS)
                or (re.search(ignore_classes_pattern, class_str, flags=re.IGNORECASE))
                or (re.search(ignore_classes_pattern, id_str, flags=re.IGNORECASE))
            ):
                element.decompose()
                removed_element_counts += 1

        logger.mesg(
            f"- Elements: "
            f'{colored(len(soup.find_all()),"light_green")} / {colored(removed_element_counts,"light_red")}'
        )

        html_str = str(soup)
        self.html_str = html_str

        return self.html_str

    def extract(self, html_path):
        logger.note(f"Extracting content from: {html_path}")

        if not Path(html_path).exists():
            logger.warn(f"File not found: {html_path}")
            return ""

        encodings = ["utf-8", "latin-1"]
        for encoding in encodings:
            try:
                with open(html_path, "r", encoding=encoding, errors="ignore") as rf:
                    html_str = rf.read()
                break
            except UnicodeDecodeError:
                pass
        else:
            logger.warn(f"No matching encodings: {html_path}")
            return ""

        html_str = self.remove_elements_from_html(html_str)
        markdown_str = self.html_to_markdown(html_str)
        return markdown_str


class BatchWebpageContentExtractor:
    def __init__(self) -> None:
        self.html_path_and_extracted_content_list = []
        self.done_count = 0

    def extract_single_html(self, html_path):
        webpage_content_extractor = WebpageContentExtractor()
        extracted_content = webpage_content_extractor.extract(html_path)
        self.html_path_and_extracted_content_list.append(
            {"html_path": html_path, "extracted_content": extracted_content}
        )
        self.done_count += 1
        logger.success(
            f"> [{self.done_count}/{self.total_count}] Extracted: {html_path}"
        )

    def extract(self, html_paths):
        self.html_path = html_paths
        self.total_count = len(self.html_path)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.extract_single_html, html_path)
                for html_path in self.html_path
            ]
            for idx, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()

        return self.html_path_and_extracted_content_list





# What characters are forbidden in Windows and Linux directory names?
#   https://stackoverflow.com/questions/1976007/what-characters-are-forbidden-in-windows-and-linux-directory-names

INVALID_FILE_PATH_CHARS = [
    "\\",
    "/",
    ":",
    "*",
    "?",
    '"',
    "<",
    ">",
    "|",
    "\n",
    "\t",
    "\r",
    *[chr(i) for i in range(32)],
]

WINDOWS_INVALID_FILE_PATH_NAMES = [
    "con",
    "prn",
    "aux",
    "nul",
    *[f"com{i+1}" for i in range(10)],
    *[f"lpt{i+1}" for i in range(10)],
]


class FilepathConverter:
    def __init__(self, parent: str = None):
        self.output_root = Path(__file__).parents[1] / "files"
        self.parent = parent

    def preprocess(self, input_string):
        return input_string

    def validate(self, input_string):
        if not input_string:
            return input_string
        filename = input_string
        for char in INVALID_FILE_PATH_CHARS:
            filename = filename.replace(char, "_")
        if platform.system() == "Windows":
            filename_base = filename.split(".")[0]
            if filename_base.lower() in WINDOWS_INVALID_FILE_PATH_NAMES:
                filename_base = filename_base + "_"
                filename = ".".join([filename_base, *filename.split(".")[1:]])
        return filename

    def append_extension(self, filename, accept_exts=[".html", ".htm"], ext=".html"):
        if ext:
            filename_ext = "." + filename.split(".")[-1]
            if filename_ext.lower() not in accept_exts:
                filename += ext
        return filename

    def convert(self, input_string, parent=None):
        filename = self.preprocess(input_string)
        filename = self.validate(filename)
        filename = self.append_extension(filename)

        parent = parent or self.parent
        parent = self.validate(parent)
        if parent:
            filepath = self.output_root / parent / filename
        else:
            filepath = self.output_root / filename

        self.filename = filename
        self.filepath = filepath

        return self.filepath


class UrlToFilepathConverter(FilepathConverter):
    def __init__(self, parent: str = None):
        super().__init__(parent)
        self.output_root = self.output_root / "urls"

    def preprocess(self, url):
        filename = unquote(url.split("//")[1])
        return filename


class QueryToFilepathConverter(FilepathConverter):
    def __init__(self, parent: str = None):
        super().__init__(parent)
        self.output_root = self.output_root / "queries"


def add_fillers(text, filler="=", fill_side="both"):
    terminal_width = shutil.get_terminal_size().columns
    text = text.strip()
    text_width = len(text)
    if text_width >= terminal_width:
        return text

    if fill_side[0].lower() == "b":
        leading_fill_str = filler * ((terminal_width - text_width) // 2 - 1) + " "
        trailing_fill_str = " " + filler * (
            terminal_width - text_width - len(leading_fill_str) - 1
        )
    elif fill_side[0].lower() == "l":
        leading_fill_str = filler * (terminal_width - text_width - 1) + " "
        trailing_fill_str = ""
    elif fill_side[0].lower() == "r":
        leading_fill_str = ""
        trailing_fill_str = " " + filler * (terminal_width - text_width - 1)
    else:
        raise ValueError("Invalid fill_side")

    filled_str = f"{leading_fill_str}{text}{trailing_fill_str}"
    return filled_str


class OSLogger(logging.Logger):
    LOG_METHODS = {
        "err": ("error", "red"),
        "warn": ("warning", "light_red"),
        "note": ("info", "light_magenta"),
        "mesg": ("info", "light_cyan"),
        "file": ("info", "light_blue"),
        "line": ("info", "white"),
        "success": ("info", "light_green"),
        "fail": ("info", "light_red"),
        "back": ("debug", "light_cyan"),
    }
    INDENT_METHODS = [
        "indent",
        "set_indent",
        "reset_indent",
        "store_indent",
        "restore_indent",
        "log_indent",
    ]
    LEVEL_METHODS = [
        "set_level",
        "store_level",
        "restore_level",
        "quiet",
        "enter_quiet",
        "exit_quiet",
    ]
    LEVEL_NAMES = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    def __init__(self, name=None, prefix=False):
        if not name:
            frame = inspect.stack()[1]
            module = inspect.getmodule(frame[0])
            name = module.__name__

        super().__init__(name)
        self.setLevel(logging.INFO)

        if prefix:
            formatter_prefix = "[%(asctime)s] - [%(name)s] - [%(levelname)s]\n"
        else:
            formatter_prefix = ""

        self.formatter = logging.Formatter(formatter_prefix + "%(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(self.formatter)
        self.addHandler(stream_handler)

        self.log_indent = 0
        self.log_indents = []

        self.log_level = "info"
        self.log_levels = []

    def indent(self, indent=2):
        self.log_indent += indent

    def set_indent(self, indent=2):
        self.log_indent = indent

    def reset_indent(self):
        self.log_indent = 0

    def store_indent(self):
        self.log_indents.append(self.log_indent)

    def restore_indent(self):
        self.log_indent = self.log_indents.pop(-1)

    def set_level(self, level):
        self.log_level = level
        self.setLevel(self.LEVEL_NAMES[level])

    def store_level(self):
        self.log_levels.append(self.log_level)

    def restore_level(self):
        self.log_level = self.log_levels.pop(-1)
        self.set_level(self.log_level)

    def quiet(self):
        self.set_level("critical")

    def enter_quiet(self, quiet=False):
        if quiet:
            self.store_level()
            self.quiet()

    def exit_quiet(self, quiet=False):
        if quiet:
            self.restore_level()

    def log(
        self,
        level,
        color,
        msg,
        indent=0,
        fill=False,
        fill_side="both",
        end="\n",
        *args,
        **kwargs,
    ):
        if type(msg) == str:
            msg_str = msg
        else:
            msg_str = repr(msg)
            quotes = ["'", '"']
            if msg_str[0] in quotes and msg_str[-1] in quotes:
                msg_str = msg_str[1:-1]

        indent_str = " " * (self.log_indent + indent)
        indented_msg = "\n".join([indent_str + line for line in msg_str.split("\n")])

        if fill:
            indented_msg = add_fillers(indented_msg, fill_side=fill_side)

        handler = self.handlers[0]
        handler.terminator = end

        getattr(self, level)(colored(indented_msg, color), *args, **kwargs)

    def route_log(self, method, msg, *args, **kwargs):
        level, method = method
        functools.partial(self.log, level, method, msg)(*args, **kwargs)

    def err(self, msg: str = "", *args, **kwargs):
        self.route_log(("error", "red"), msg, *args, **kwargs)

    def warn(self, msg: str = "", *args, **kwargs):
        self.route_log(("warning", "light_red"), msg, *args, **kwargs)

    def note(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_magenta"), msg, *args, **kwargs)

    def mesg(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_cyan"), msg, *args, **kwargs)

    def file(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_blue"), msg, *args, **kwargs)

    def line(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "white"), msg, *args, **kwargs)

    def success(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_green"), msg, *args, **kwargs)

    def fail(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_red"), msg, *args, **kwargs)

    def back(self, msg: str = "", *args, **kwargs):
        self.route_log(("debug", "light_cyan"), msg, *args, **kwargs)


logger = OSLogger()


def shell_cmd(cmd, getoutput=False, showcmd=True, env=None):
    if showcmd:
        logger.info(colored(f"\n$ [{os.getcwd()}]", "light_blue"))
        logger.info(colored(f"  $ {cmd}\n", "light_cyan"))
    if getoutput:
        output = subprocess.getoutput(cmd, env=env)
        return output
    else:
        subprocess.run(cmd, shell=True, env=env)


class Runtimer:
    def __enter__(self):
        self.t1, _ = self.start_time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.t2, _ = self.end_time()
        self.elapsed_time(self.t2 - self.t1)

    def start_time(self):
        t1 = datetime.datetime.now()
        self.logger_time("start", t1)
        return t1, self.time2str(t1)

    def end_time(self):
        t2 = datetime.datetime.now()
        self.logger_time("end", t2)
        return t2, self.time2str(t2)

    def elapsed_time(self, dt=None):
        if dt is None:
            dt = self.t2 - self.t1
        self.logger_time("elapsed", dt)
        return dt, self.time2str(dt)

    def logger_time(self, time_type, t):
        time_types = {
            "start": "Start",
            "end": "End",
            "elapsed": "Elapsed",
        }
        time_str = add_fillers(
            colored(
                f"{time_types[time_type]} time: [ {self.time2str(t)} ]",
                "light_magenta",
            ),
            fill_side="both",
        )
        logger.line(time_str)

    # Convert time to string
    def time2str(self, t):
        datetime_str_format = "%Y-%m-%d %H:%M:%S"
        if isinstance(t, datetime.datetime):
            return t.strftime(datetime_str_format)
        elif isinstance(t, datetime.timedelta):
            hours = t.seconds // 3600
            hour_str = f"{hours} hr" if hours > 0 else ""
            minutes = (t.seconds // 60) % 60
            minute_str = f"{minutes:>2} min" if minutes > 0 else ""
            seconds = t.seconds % 60
            second_str = f"{seconds:>2} s"
            time_str = " ".join([hour_str, minute_str, second_str]).strip()
            return time_str
        else:
            return str(t)


class OSEnver:
    def __init__(self):
        self.envs_stack = []
        self.envs = os.environ.copy()

    def store_envs(self):
        self.envs_stack.append(self.envs)

    def restore_envs(self):
        self.envs = self.envs_stack.pop()

    def set_envs(self, secrets=True, proxies=None, store_envs=True):
        # caller_info = inspect.stack()[1]
        # logger.back(f"OS Envs is set by: {caller_info.filename}")

        if store_envs:
            self.store_envs()

        if secrets:
            secrets_path = Path(__file__).parents[1] / "secrets.json"
            if secrets_path.exists():
                with open(secrets_path, "r") as rf:
                    secrets = json.load(rf)
            else:
                secrets = {}

        if proxies:
            for proxy_env in ["http_proxy", "https_proxy"]:
                if isinstance(proxies, str):
                    self.envs[proxy_env] = proxies
                elif "http_proxy" in secrets.keys():
                    self.envs[proxy_env] = secrets["http_proxy"]
                elif os.getenv("http_proxy"):
                    self.envs[proxy_env] = os.getenv("http_proxy")
                else:
                    continue

        self.proxy = (
            self.envs.get("all_proxy")
            or self.envs.get("http_proxy")
            or self.envs.get("https_proxy")
            or None
        )
        self.requests_proxies = {
            "http": self.proxy,
            "https": self.proxy,
        }

        if self.proxy:
            logger.note(f"Using proxy: [{self.proxy}]")


enver = OSEnver()

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


IGNORE_TAGS = ["script", "style", "button"]
IGNORE_CLASSES = [
    # common
    "sidebar",
    "footer",
    "related",
    "comment",
    "topbar",
    "offcanvas",
    "navbar",
    # 163.com
    "post_(top)|(side)|(recommends)|(crumb)|(statement)|(next)|(jubao)",
    "ntes\-.*nav",
    "nav\-bottom",
    # wikipedia.org
    "language\-list",
    "vector\-(header)|(column)|(sticky\-pinned)|(dropdown\-content)",
    "navbox",
    "catlinks",
]

IGNORE_HOSTS = [
    "weibo.com",
    "hymson.com",
    "yahoo.com",
]

REQUESTS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62",
}




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


