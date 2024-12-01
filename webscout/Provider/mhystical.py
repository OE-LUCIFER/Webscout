import requests
import json
from typing import Any, Dict, Optional, Generator, List

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions


class Mhystical(Provider):
    """
    A class to interact with the Mhystical API. Improved to meet webscout provider standards.
    """

    AVAILABLE_MODELS = ["gpt-4", "gpt-3.5-turbo"]  # Add available models

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
        model: str = "gpt-4", # Default model
        system_prompt: str = "You are a helpful AI assistant." # Default system prompt
    ):
        """Initializes the Mhystical API."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://api.mhystical.cc/v1/completions"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt # Store system prompt
        self.headers = {
            "x-api-key": "mhystical", # Set API key in header (or better, in __init__ from parameter)
            "Content-Type": "application/json",
            "accept": "*/*",
            "user-agent": "Mozilla/5.0"
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
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:

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

        messages = [
                {"role": "system", "content": self.system_prompt},  # Include system prompt
                {"role": "user", "content": conversation_prompt},
            ]
            
        data = {
            "model": self.model,  # Now using self.model
            "messages": messages # Pass messages to API
        }

        def for_stream():
            try:
                with requests.post(self.api_endpoint, headers=self.headers, json=data, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status() # Raise exceptions for HTTP errors

                    # Emulate streaming for this API
                    full_response = ""  # Accumulate the full response
                    for chunk in response.iter_content(decode_unicode=True, chunk_size=self.stream_chunk_size):
                        if chunk:
                            full_response += chunk
                            yield chunk if raw else {"text": chunk}

                    self.last_response.update({"text": full_response})
                    self.conversation.update_chat_history(prompt, full_response)
            except requests.exceptions.RequestException as e:
                raise exceptions.ProviderConnectionError(f"Network error: {str(e)}")

        def for_non_stream():
            try:
                response = self.session.post(self.api_endpoint, headers=self.headers, json=data, timeout=self.timeout)
                response.raise_for_status()

                full_response = self._parse_response(response.text)
                self.last_response.update({"text": full_response})

                # Yield the entire response as a single chunk
                yield {"text": full_response}

            except requests.exceptions.RequestException as e:
                raise exceptions.ProviderConnectionError(f"Network error: {str(e)}")

        return for_stream() if stream else for_non_stream()



    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:

        def for_stream():
            for response in self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            response = next(self.ask(
                prompt, stream=False, optimizer=optimizer, conversationally=conversationally
            ))
            return self.get_message(response)
        return for_stream() if stream else for_non_stream()



    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

    @staticmethod
    def _parse_response(response_text: str) -> str:
        """Parse and validate API response."""
        try:
            data = json.loads(response_text)
            return data["choices"][0]["message"]["content"].strip()
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise exceptions.InvalidResponseError(f"Failed to parse response: {str(e)}")

if __name__ == "__main__":
    from rich import print
    ai = Mhystical()
    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)