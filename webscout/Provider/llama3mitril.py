import requests
import json
import re
from typing import Any, Dict, Optional, Generator
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions


class Llama3Mitril(Provider):
    """
    A class to interact with the Llama3 Mitril API. Implements the WebScout provider interface.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2048,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        system_prompt: str = "You are a helpful, respectful and honest assistant.",
        temperature: float = 0.8,
    ):
        """Initializes the Llama3Mitril API."""
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api_endpoint = "https://llama3.mithrilsecurity.io/generate_stream"
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.headers = {
            "Content-Type": "application/json",
            "DNT": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
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
            is_conversation, self.max_tokens, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.session.proxies = proxies

    def _format_prompt(self, prompt: str) -> str:
        """Format the prompt for the Llama3 model"""
        return (
            f"<|begin_of_text|>"
            f"<|start_header_id|>system<|end_header_id|>{self.system_prompt}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>{prompt}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|><|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>"
        )

    def ask(
        self,
        prompt: str,
        stream: bool = True,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """Sends a prompt to the Llama3 Mitril API and returns the response."""
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

        data = {
            "inputs": self._format_prompt(conversation_prompt),
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "return_full_text": False
            }
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint,
                headers=self.headers,
                json=data,
                stream=True,
                timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        chunk = json.loads(line.split('data: ')[1])
                        if token_text := chunk.get('token', {}).get('text'):
                            if '<|eot_id|>' not in token_text:
                                streaming_response += token_text
                                yield token_text if raw else {"text": token_text}
                    except (json.JSONDecodeError, IndexError) as e:
                        continue

            self.last_response.update({"text": streaming_response})
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            full_response = ""
            for chunk in for_stream():
                full_response += chunk if raw else chunk['text']
            return {"text": full_response}

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = True,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:
        """Generates a response from the Llama3 Mitril API."""

        def for_stream():
            for response in self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt, stream=False, optimizer=optimizer, conversationally=conversationally
                )
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Dict[str, Any]) -> str:
        """Extracts the message from the API response."""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]


if __name__ == "__main__":
    from rich import print
    
    ai = Llama3Mitril(
        max_tokens=2048,
        temperature=0.8,
        timeout=30
    )

    for response in ai.chat("Hello", stream=True):
        print(response)