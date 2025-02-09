import requests
import re
from typing import Any, Dict, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions


class DGAFAI(Provider):
    """
    A class to interact with the DGAF.ai API.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """Initializes the DGAFAI API client."""
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://www.dgaf.ai/api/chat"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "cookie": "_ga=GA1.1.1717609725.1738729535; _ga_52CD0XKYNM=GS1.1.1738729535.1.0.1738729546.0.0.0",
            "dnt": "1",
            "origin": "https://www.dgaf.ai",
            "referer": "https://www.dgaf.ai/?via=topaitools",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
            ),
        }
        self.session.headers.update(self.headers)
        self.session.proxies = proxies
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator[str, None, None]:
        """Chat with AI
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            Union[Dict, Generator[Dict, None, None]]: Response generated
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ]
        }

        def for_stream():
            try:
                with self.session.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                ) as response:
                    response.raise_for_status()  # Check for HTTP errors

                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            match = re.search(r'0:"(.*?)"', line)
                            if match:
                                content = match.group(1)
                                if content:
                                    streaming_text += content
                                    yield content if raw else dict(text=content)

                    self.last_response.update(dict(text=streaming_text))
                    self.conversation.update_chat_history(
                        prompt, self.get_message(self.last_response)
                    )

            except requests.exceptions.RequestException as e:
                raise exceptions.ProviderConnectionError(f"Request failed: {e}")

        def for_non_stream():
            full_response = ""
            for chunk in for_stream():
                full_response += chunk if raw else chunk["text"]
            return {"text": full_response}

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
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
        return response["text"].replace("\\n", "\n").replace("\\n\\n", "\n\n")

    # @staticmethod
    # def clean_content(text: str) -> str:
    #     cleaned_text = re.sub(r'\[REF\]\(https?://[^\s]*\)', '', text)
    #     return cleaned_text


if __name__ == "__main__":
    from rich import print

    ai = DGAFAI()
    response = ai.chat("write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
