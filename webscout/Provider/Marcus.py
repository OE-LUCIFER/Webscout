import requests
import json
from typing import Any, Dict, Optional, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout import LitAgent as Lit

class Marcus(Provider):
    """
    This class provides methods for interacting with the AskMarcus API.
    Improved to match webscout provider standards with comprehensive logging.
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
        logging: bool = False
    ):
        """Initializes the Marcus API with logging capabilities."""
        self.logger = LitLogger(
            name="Marcus",
            format=LogFormat.MODERN_EMOJI,
            color_scheme=ColorScheme.CYBERPUNK
        ) if logging else None

        if self.logger:
            self.logger.info("Initializing Marcus API")

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
            'user-agent': Lit().random(),
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

        if self.logger:
            self.logger.info("Marcus API initialized successfully")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator[str, None, None]:
        """Sends a prompt to the AskMarcus API and returns the response with logging."""
        if self.logger:
            self.logger.debug(f"Processing request - Prompt: {prompt[:50]}...")
            self.logger.debug(f"Stream: {stream}, Optimizer: {optimizer}")

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
                if self.logger:
                    self.logger.debug(f"Applied optimizer: {optimizer}")
            else:
                if self.logger:
                    self.logger.error(f"Invalid optimizer requested: {optimizer}")
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        data = {"message": conversation_prompt}

        def for_stream():
            try:
                if self.logger:
                    self.logger.debug("Initiating streaming request to API")

                with requests.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=data,
                    stream=True,
                    timeout=self.timeout
                ) as response:
                    response.raise_for_status()
                    
                    if self.logger:
                        self.logger.info(f"API connection established successfully. Status: {response.status_code}")

                    for line in response.iter_lines():
                        if line:
                            yield line.decode('utf-8')
                    
                    self.conversation.update_chat_history(
                        prompt, self.get_message(self.last_response)
                    )

            except requests.exceptions.RequestException as e:
                if self.logger:
                    self.logger.error(f"API request failed: {str(e)}")
                raise exceptions.ProviderConnectionError(f"Error connecting to Marcus: {str(e)}")

        def for_non_stream():
            if self.logger:
                self.logger.debug("Processing non-streaming request")
            
            full_response = ""
            for line in for_stream():
                full_response += line
            self.last_response = {"text": full_response}
            
            if self.logger:
                self.logger.debug("Response processing completed")
            
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:
        """Generates a response from the AskMarcus API with logging."""
        if self.logger:
            self.logger.debug(f"Chat request initiated - Prompt: {prompt[:50]}...")

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

if __name__ == "__main__":
    from rich import print
    # Enable logging for testing
    ai = Marcus(logging=True)
    response = ai.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
