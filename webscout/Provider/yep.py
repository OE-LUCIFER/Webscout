import time
import uuid
import cloudscraper
import json

from typing import Any, Dict, Optional, Generator, Union
from dataclasses import dataclass, asdict
from datetime import date

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import WEBS, exceptions
from webscout.Litlogger import Logger, LogFormat
from webscout.litagent import LitAgent


class YEPCHAT(Provider):
    """
    YEPCHAT is a provider class for interacting with the Yep API.

    Attributes:
        AVAILABLE_MODELS (list): List of available models for the provider.
    """

    AVAILABLE_MODELS = ["DeepSeek-R1-Distill-Qwen-32B"]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 1280,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "DeepSeek-R1-Distill-Qwen-32B",
        temperature: float = 0.6,
        top_p: float = 0.7,
        logging: bool = False,
    ):
        """
        Initializes the YEPCHAT provider with the specified parameters.

        Examples:
            >>> ai = YEPCHAT(logging=True)
            >>> ai.ask("What's the weather today?")
            Sends a prompt to the Yep API and returns the response.

            >>> ai.chat("Tell me a joke", stream=True)
            Initiates a chat with the Yep API using the provided prompt.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}"
            )

        self.session = cloudscraper.create_scraper()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://api.yep.com/v1/chat/completions"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()

        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json; charset=utf-8",
            "DNT": "1",
            "Origin": "https://yep.com",
            "Referer": "https://yep.com/",
            "Sec-CH-UA": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "User-Agent": self.agent.random(),  # Use LitAgent to generate a random user agent
        }
        self.cookies = {"__Host-session": uuid.uuid4().hex}

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method))
            and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(act, raise_not_found=True, default=None, case_insensitive=True)
            if act
            else intro or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.session.proxies = proxies

        self.knowledge_cutoff = "December 2023"

        # Initialize logger
        self.logger = Logger(name="YEPCHAT", format=LogFormat.MODERN_EMOJI) if logging else None

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        """
        Sends a prompt to the Yep API and returns the response.

        Examples:
            >>> ai = YEPCHAT()
            >>> ai.ask("What's the weather today?")
            Returns the response from the Yep API.

            >>> ai.ask("Tell me a joke", stream=True)
            Streams the response from the Yep API.
        """
        if self.logger:
            self.logger.debug(f"ask() called with prompt: {prompt}")

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                if self.logger:
                    self.logger.error(f"Invalid optimizer: {optimizer}")
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        data = {
            "stream": stream,
            "max_tokens": self.max_tokens_to_sample,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "messages": [{"content": conversation_prompt, "role": "user"}],
            "model": self.model,
        }

        def for_stream():
            try:
                with self.session.post(self.chat_endpoint, headers=self.headers, cookies=self.cookies, json=data, stream=True, timeout=self.timeout) as response:
                    if not response.ok:
                        if self.logger:
                            self.logger.error(f"Failed to generate response: {response.status_code} {response.reason}")
                        raise exceptions.FailedToGenerateResponseError(
                            f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                        )

                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            line = line.strip()
                            if line.startswith("data: "):
                                json_str = line[6:]
                                if json_str == "[DONE]":
                                    break
                                try:
                                    json_data = json.loads(json_str)
                                    if 'choices' in json_data:
                                        choice = json_data['choices'][0]
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            content = choice['delta']['content']
                                            streaming_text += content
                                            
                                            # Yield ONLY the new content:
                                            resp = dict(text=content) 
                                            yield resp if raw else resp
                                except json.JSONDecodeError:
                                    if self.logger:
                                        self.logger.warning("JSONDecodeError encountered.")
                                    pass
                    self.conversation.update_chat_history(prompt, streaming_text)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Request failed: {e}")
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """
        Initiates a chat with the Yep API using the provided prompt.

        Examples:
            >>> ai = YEPCHAT()
            >>> ai.chat("Tell me a joke")
            Returns the chat response from the Yep API.

            >>> ai.chat("What's the weather today?", stream=True)
            Streams the chat response from the Yep API.
        """
        if self.logger:
            self.logger.debug(f"chat() called with prompt: {prompt}")

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
        """
        Extracts the message content from the API response.

        Examples:
            >>> ai = YEPCHAT()
            >>> response = ai.ask("Tell me a joke")
            >>> ai.get_message(response)
            Extracts and returns the message content from the response.
        """
        assert isinstance(response, dict)
        return response["text"]


if __name__ == "__main__":
    from rich import print

    ai = YEPCHAT(logging=False)

    response = ai.chat("how many r in 'strawberry'", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
