import requests
import secrets
from typing import Dict, Generator, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent


class GeminiPro(Provider):
    """
    A class to interact with the Minitool AI API.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Initializes the Minitool AI API client."""
        self.url = "https://minitoolai.com/test_python/"
        self.headers = {
            "authority": "minitoolai.com",
            "method": "POST",
            "path": "/test_python/",
            "scheme": "https",
            "accept": "*/*",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://minitoolai.com",
            "priority": "u=1, i",
            "referer": "https://minitoolai.com/Gemini-Pro/",
            "sec-ch-ua": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": LitAgent().random(),
            "x-requested-with": "XMLHttpRequest",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.last_response = {}

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
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
    ) -> Union[Dict, Generator]:
        """Sends a chat completion request to the Minitool AI API."""

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

        payload = {"utoken": secrets.token_hex(32), "message": conversation_prompt}

        def for_stream():
            # MinitoolAI doesn't support streaming; emulate with a single yield
            try:
                response = self.session.post(
                    self.url, json=payload, timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                text = data.get(
                    "response", ""
                )  # Get response, default to "" if missing
                self.last_response.update({"text": text})
                yield {"text": text}  # Yield the entire response
            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")
            self.conversation.update_chat_history(prompt, text)  # Update chat history

        def for_non_stream():
            for _ in for_stream():
                pass  # Update last_response
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator]:
        """Generate response `str`"""

        def for_stream():
            for response in self.ask(
                prompt,
                stream=True,
                optimizer=optimizer,
                conversationally=conversationally,
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt,
                    stream=False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response.get("text", "")  # Handle missing keys


if __name__ == "__main__":
    from rich import print

    bot = GeminiPro()
    try:
        response = bot.chat("hi", stream=True)
        for chunk in response:
            print(chunk, end="", flush=True)
    except Exception as e:
        print(f"An error occurred: {e}")
