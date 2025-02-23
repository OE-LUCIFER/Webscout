import json
import re
import requests
from typing import Generator, Optional, Union

from zope.interface import provider


class Response:
    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text

def extract_content(data_lines):
    if not data_lines:
        return []
    content_list = []
    for line in data_lines:
        try:
            if not isinstance(line, (str, bytes)):
                continue
            if line.startswith("data:"):
                line = line[len("data:"):].strip()
            data = json.loads(line)
            if 'data' in data and isinstance(data['data'], str):
                try:
                    nested_data = json.loads(data['data'])
                    data.update(nested_data)
                except json.JSONDecodeError:
                    pass
            if 'content' in data:
                try:
                    content = data['content']
                    if isinstance(content, str):
                        content_list.append(content)
                except KeyError:
                    pass
        except (json.JSONDecodeError, KeyError):
            continue
    return content_list

class Isou:
    def __init__(
            self,
            timeout: int = 120,
            proxies: Optional[dict] = None,
    ):
        self.available_models = ["siliconflow:deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
                                 "siliconflow:Qwen/Qwen2.5-72B-Instruct-128K",
                                 "deepseek-reasoner"]
        self.session = requests.Session()
        def close(self):
            """Close the session and release resources"""
            if self.session:
                self.session.close()
        self.chat_endpoint = "https://isou.chat/api/search"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.full_text = {}
        self.model = self.available_models[0]
        self.provider = "siliconflow"
        self.mode = "simple" # deep
        self.catigories = "general"# science
        self.reload = False
        refer = f"https://isou.chat/search?q=hi"
        self.headers = {
            "accept": "text/event-stream",
            "pragma": "no-cache",
            "referer": refer,
            "accept-language": "ru-RU,ru;q=0.6",
            "content-type": "application/json",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }
        self.session.headers.update(self.headers)
        self.proxies = proxies

    def search(
            self,
            prompt: str,
            stream: bool = False,
            raw: bool = False,
    ) -> Union[dict, Generator[dict, None, None]]:
        if self.model == self.available_models[0] or self.model == self.available_models[1]:
            self.provider = "siliconflow"
        else:
            self.provider = "deepseek"
        payload = {
            "categories": [self.catigories],
            "engine": "SEARXNG",
            "language": "all",
            "mode": self.mode,
            "model": self.model,
            "provider": self.provider,
            "reload": self.reload,
            "stream": stream,
        }
        params = {"q": prompt}
        return self.generate_response(payload, params, stream=stream, raw=raw)

    def generate_response(
            self, payload, params, stream=False, raw=False
    ) -> Generator[dict, None, None]:
        def for_stream() -> Generator[dict, None, None]:
            full_text = ""
            links = []
            try:
                with self.session.post(
                        self.chat_endpoint,
                        params=params,
                        json=payload,
                        stream=True,
                        timeout=self.timeout,
                ) as response:
                    if not response.ok:
                        raise Exception(
                            f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                        )
                    for line in response.iter_lines(chunk_size=self.stream_chunk_size, decode_unicode=False):
                        if not line.startswith(b'data:'):
                            continue
                        try:
                            line_data = line[len(b'data:'):].strip().decode('utf-8')
                            data = json.loads(line_data)
                            if 'data' in data and isinstance(data['data'], str):
                                try:
                                    nested_data = json.loads(data['data'])
                                    data.update(nested_data)
                                except json.JSONDecodeError:
                                    pass
                            if 'content' in data:
                                content = data['content']
                                if isinstance(content, str):
                                    full_text += content
                            if 'image' in data and 'url' in data['image']:
                                links.append(data['image']['url'])
                            if 'context' in data and 'url' in data['context']:
                                links.append(data['context']['url'])
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                    yield {"text": full_text.strip(), "links": list(set(links))}
            except requests.exceptions.RequestException as e:
                raise Exception(f"Request failed: {e}")

        return for_stream()

def replace_links_with_numbers(text, links):
    link_map = {f"citation:{i}]]": f"[{i}]" for i, link in enumerate(links, start=1)}
    pattern = r"citation:\d+]]"

    def replace_func(match):
        for key in link_map:
            if key in match.group(0):
                return link_map[key]
        return match.group(0)

    result_text = re.sub(pattern, replace_func, text)
    result_text = result_text.replace("[[[", "[")

    link_list = "\n".join([f"{i}. {link}" for i, link in enumerate(links, start=1)])
    return f"{result_text}\n\nСсылки:\n{link_list}"

if __name__ == "__main__":
    from rich import print
    ai = Isou()
    ai.model= ai.available_models[2]
    response = ai.search(input(">>>"), stream=True, raw=False)
    all_text = ""
    all_links = []
    for chunk in response:
        text = chunk.get("text", "")
        links = chunk.get("links", [])
        all_text += text
        all_links.extend(links)

    unique_links = list(set(all_links))

    all_text = re.sub(r'\s+', ' ', all_text).strip()
    final_text = replace_links_with_numbers(all_text, unique_links)
    print(final_text)
