import requests
import json
import os
from typing import Any, Dict, Optional, Generator, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions

class Bagoodex(Provider):
    """
    A class to interact with the Bagoodex API.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,  # Set a reasonable default
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Initializes the Bagoodex API client."""
        self.url = "https://bagoodex.io/front-api/chat"
        self.headers = {"Content-Type": "application/json"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)  # Use provided proxies
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
    ) -> Union[Dict[str, Any], Generator[Any, None, None]]:
        """Sends a chat completion request to the Bagoodex API."""

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")


        payload = {
            "prompt": "You are AI",  # This seems to be required by the API
            "messages": [{"content": "Hi, this is chatgpt, let's talk", "role": "assistant"}],
            "input": conversation_prompt,
        }

        def for_stream():
            try:
                response = self.session.post(self.url, json=payload, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                text = response.text
                self.last_response.update({"text": text})

                if stream:
                    for char in text:
                        yield {"text": char}  # Yielding one character at a time for streaming
                else:
                    yield {"text": text}

            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:  # Catch JSON errors too
                raise exceptions.FailedToGenerateResponseError(f"Error during request: {e}")
            self.conversation.update_chat_history(prompt, self.get_message(self.last_response))

        def for_non_stream():
            for _ in for_stream(): pass
            return self.last_response


        return for_stream() if stream else for_non_stream()




    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:


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


    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response.get("text", "")


if __name__ == "__main__":
    from rich import print
    ai = Bagoodex()
    response = ai.chat("write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)