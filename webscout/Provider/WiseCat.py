import requests
import json
from typing import Any, Dict, Generator, Optional

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent
from webscout import Logger
from webscout import LogFormat



class WiseCat(Provider):
    """
    A class to interact with the WiseCat API.
    """

    AVAILABLE_MODELS = [
        "chat-model-small",
        "chat-model-large",
        "chat-model-reasoning",
    ]

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
        model: str = "chat-model-large",
        system_prompt: str = "You are a helpful AI assistant.",
        logging: bool = False,
    ):
        """Initializes the WiseCat API client."""

        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://wise-cat-groq.vercel.app/api/chat"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": LitAgent().random()
        }
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

        # Initialize logger
        self.logger = Logger(name="WISECAT", format=LogFormat.MODERN_EMOJI) if logging else None

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
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """Chat with AI"""
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

        payload = {
            "id": "ephemeral",
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": conversation_prompt,
                }
            ],
            "selectedChatModel": self.model
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint, headers=self.headers, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                error_msg = f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                if self.logger:
                    self.logger.error(error_msg)
                raise exceptions.FailedToGenerateResponseError(error_msg)

            streaming_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("0:"):
                        content = line[2:].strip('"')
                        streaming_response += content
                        yield content if raw else dict(text=content)
            
            self.last_response.update(dict(text=streaming_response))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

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
        """Generate response `str`"""
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
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    ai = WiseCat()
    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)
