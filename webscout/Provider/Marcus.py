import requests
import json
from typing import Any, Dict, Optional, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions


class Marcus(Provider):
    """
    This class provides methods for interacting with the AskMarcus API.
    Improved to match webscout provider standards.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2048,  # Added max_tokens parameter
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Initializes the Marcus API."""
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://www.askmarcus.app/api/response"
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            'content-type': 'application/json',
            'accept': '*/*',
            'origin': 'https://www.askmarcus.app',
            'referer': 'https://www.askmarcus.app/chat',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
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
        self.session.proxies = proxies

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator[str, None, None]:
        """Sends a prompt to the AskMarcus API and returns the response."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        data = {"message": conversation_prompt}

        def for_stream():
            try:
                with requests.post(self.api_endpoint, headers=self.headers, json=data, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield line.decode('utf-8')
                    self.conversation.update_chat_history(prompt, self.get_message(self.last_response))

            except requests.exceptions.RequestException as e:
                raise exceptions.ProviderConnectionError(f"Error connecting to Marcus: {str(e)}")

        def for_non_stream():
            full_response = ""
            for line in for_stream():
                full_response += line
            self.last_response = {"text": full_response}
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:
        """Generates a response from the AskMarcus API."""

        def for_stream():
            for response_chunk in self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            ):
                yield response_chunk

        def for_non_stream():
            response = self.ask(
                prompt, stream=False, optimizer=optimizer, conversationally=conversationally
            )
            return self.get_message(response)

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Dict[str, Any]) -> str:
        """Extracts the message from the API response."""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response.get("text", "")

if __name__ == '__main__':
    ai = Marcus(timeout=30)
    response = ai.chat("Tell me about India", stream=True)
    for chunk in response:
        print(chunk)
