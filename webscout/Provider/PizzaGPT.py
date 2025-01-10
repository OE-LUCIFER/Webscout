import requests
from typing import Any, AsyncGenerator, Dict, Optional, Union, Generator
import json

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from webscout import LitAgent as Lit
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme

class PIZZAGPT(Provider):
    """
    PIZZAGPT is a provider class for interacting with the PizzaGPT API.

    Attributes:
        knowledge_cutoff (str): The knowledge cutoff date for the model
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
        logging: bool = False,
    ) -> None:
        """
        Initializes the PizzaGPT provider with the specified parameters.

        Examples:
            >>> ai = PIZZAGPT(logging=True)
            >>> ai.ask("What's the weather today?")
            Sends a prompt to the PizzaGPT API and returns the response.

            >>> ai.chat("Tell me a joke")
            Initiates a chat with the PizzaGPT API using the provided prompt.
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://www.pizzagpt.it/api/chatx-completion"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-length": "17",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://www.pizzagpt.it",
            "priority": "u=1, i",
            "referer": "https://www.pizzagpt.it/en",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": Lit().random(),
            "x-secret": "Marinara"
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
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
        
        # Initialize logger
        self.logger = LitLogger(name="PIZZAGPT", format=LogFormat.MODERN_EMOJI, color_scheme=ColorScheme.CYBERPUNK) if logging else None


    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        """
        Sends a prompt to the PizzaGPT API and returns the response.

        Examples:
            >>> ai = PIZZAGPT()
            >>> ai.ask("What's the weather today?")
            Returns the response from the PizzaGPT API.
        """

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                if self.logger:
                    self.logger.error(f"Invalid optimizer: {optimizer}")
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        self.session.headers.update(self.headers)
        payload = {"question": conversation_prompt}

        try:
            response = self.session.post(
                self.api_endpoint, json=payload, timeout=self.timeout
            )
            if self.logger:
                self.logger.debug(response)
            if not response.ok:
                if self.logger:
                    self.logger.error(f"Failed to generate response: {response.status_code} {response.reason}")
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            resp = response.json()
            if self.logger:
                self.logger.debug(resp)
            self.last_response.update(dict(text=resp['content']))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            return self.last_response

        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """
        Initiates a chat with the PizzaGPT API using the provided prompt.

        Examples:
            >>> ai = PIZZAGPT()
            >>> ai.chat("Tell me a joke")
            Returns the chat response from the PizzaGPT API.
        """

        return self.get_message(
            self.ask(
                prompt,
                optimizer=optimizer,
                conversationally=conversationally,
            )
        )

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]
if __name__ == "__main__":
    from rich import print

    ai = PIZZAGPT(logging=True) 
    # Stream the response
    response = ai.chat("hi")
    for chunk in response:
        print(chunk, end="", flush=True)