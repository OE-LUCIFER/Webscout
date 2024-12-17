import requests
import json
import re
from typing import Any, Dict, Generator, Optional

from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent


class OOAi(Provider):
    """
    A class to interact with the oo.ai API.
    """

    def __init__(
        self,
        max_tokens: int = 600,
        timeout: int = 30,
        proxies: Optional[dict] = None,
    ):
        """Initializes the OOAi API client."""
        self.session = requests.Session()
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://oo.ai/api/search"
        self.stream_chunk_size = 1024  # Adjust as needed
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Accept": "text/event-stream",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Cache-Control": "no-cache",
            "Cookie": "_ga=GA1.1.1827087199.1734256606; _ga_P0EJPHF2EG=GS1.1.1734368698.4.1.1734368711.0.0.0",
            "DNT": "1",
            "Referer": "https://oo.ai/",
            "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        self.session.headers.update(self.headers)
        self.proxies = proxies
        self.headers["User-Agent"] = LitAgent().random()

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """Chat with AI
        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Not used. Defaults to None.
            conversationally (bool, optional): Not used. Defaults to False.
        Returns:
            Union[Dict, Generator[Dict, None, None]]: Response generated
        """
        params = {
            "q": prompt,
            "lang": "en-US",
            "tz": "Asia/Calcutta",
        }

        def for_stream():
            try:
                with self.session.get(
                    self.api_endpoint,
                    params=params,
                    headers=self.headers,
                    stream=True,
                    timeout=self.timeout,
                ) as response:

                    if not response.ok:
                        raise exceptions.FailedToGenerateResponseError(
                            f"Request failed with status code {response.status_code}: {response.text}"
                        )

                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith('data: '):
                            try:
                                json_data = json.loads(line[6:])
                                if "content" in json_data:
                                    content = self.clean_content(json_data["content"])
                                    streaming_text += content
                                    yield {"text": content} if not raw else {"text": content}
                            except json.JSONDecodeError:
                                continue
                    self.last_response.update({"text": streaming_text})

            except requests.exceptions.RequestException as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:
        """Generate response `str`"""

        def for_stream():
             for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt,
                    False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

    @staticmethod
    def clean_content(text: str) -> str:
        """Removes all webblock elements with research or detail classes."""
        cleaned_text = re.sub(
            r'<webblock class="(?:research|detail)">[^<]*</webblock>', "", text
        )
        return cleaned_text

if __name__ == "__main__":
    from rich import print
    ai = OOAi()
    response = ai.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)