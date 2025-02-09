
import requests
import json
import re
from typing import Any, Dict, Optional, Generator

from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme

class JadveOpenAI(Provider):
    """
    A class to interact with the OpenAI API through jadve.com using the streaming endpoint.
    Includes optional logging capabilities.
    """

    AVAILABLE_MODELS = ["gpt-4o", "gpt-4o-mini"]

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
        model: str = "gpt-4o-mini",
        system_prompt: str = "You are a helpful AI assistant.",
        logging: bool = False
    ):
        """
        Initializes the JadveOpenAI client with optional logging support.

        Args:
            is_conversation (bool, optional): Enable conversational mode. Defaults to True.
            max_tokens (int, optional): Maximum tokens for generation. Defaults to 600.
            timeout (int, optional): HTTP request timeout in seconds. Defaults to 30.
            intro (str, optional): Introductory prompt text. Defaults to None.
            filepath (str, optional): Path to conversation history file. Defaults to None.
            update_file (bool, optional): Whether to update the conversation history file. Defaults to True.
            proxies (dict, optional): Proxies for HTTP requests. Defaults to {}.
            history_offset (int, optional): Limit for conversation history. Defaults to 10250.
            act (str|int, optional): Act key for AwesomePrompts. Defaults to None.
            model (str, optional): AI model to be used. Defaults to "gpt-4o-mini".
            system_prompt (str, optional): System prompt text. Defaults to "You are a helpful AI assistant."
            logging (bool, optional): Enable logging functionality. Defaults to False.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.logger = LitLogger(
            name="JadveOpenAI",
            format=LogFormat.MODERN_EMOJI,
            color_scheme=ColorScheme.CYBERPUNK
        ) if logging else None

        if self.logger:
            self.logger.info(f"Initializing JadveOpenAI with model: {model}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        # Streaming endpoint for jadve.com
        self.api_endpoint = "https://openai.jadve.com/stream"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt

        # Updated headers with required x-authorization header.
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://jadve.com",
            "priority": "u=1, i",
            "referer": "https://jadve.com/",
            "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": LitAgent().random(),
            "x-authorization": "Bearer"
        }
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

        self.__available_optimizers = (
            method for method in dir(Optimizers)
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

        if self.logger:
            self.logger.info("JadveOpenAI initialized successfully.")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict | Generator[dict, None, None]:
        """
        Chat with AI.

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Return raw content chunks. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Flag for conversational optimization. Defaults to False.
        Returns:
            dict or generator: A dictionary with the generated text or a generator yielding text chunks.
        """
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
                raise Exception(
                    f"Optimizer is not one of {list(self.__available_optimizers)}"
                )

        payload = {
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": conversation_prompt}]}
            ],
            "model": self.model,
            "botId": "",
            "chatId": "",
            "stream": stream,
            "temperature": 0.7,
            "returnTokensUsage": True,
            "useTools": False
        }

        def for_stream():
            if self.logger:
                self.logger.debug("Initiating streaming request to API")
            response = self.session.post(
                self.api_endpoint, headers=self.headers, json=payload, stream=True, timeout=self.timeout
            )

            if not response.ok:
                if self.logger:
                    self.logger.error(f"API request failed. Status: {response.status_code}, Reason: {response.reason}")
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            if self.logger:
                self.logger.info(f"API connection established successfully. Status: {response.status_code}")

            # Read the entire response text.
            response_text = response.text
            pattern = r'0:"(.*?)"'
            chunks = re.findall(pattern, response_text)
            streaming_text = ""
            for content in chunks:
                streaming_text += content

                yield content if raw else dict(text=content)

            self.last_response.update(dict(text=streaming_text))
            self.conversation.update_chat_history(prompt, self.get_message(self.last_response))

            if self.logger:
                self.logger.debug("Response processing completed.")

        def for_non_stream():
            if self.logger:
                self.logger.debug("Processing non-streaming request")
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
    ) -> str | Generator[str, None, None]:
        """
        Generate a chat response (string).

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Flag for conversational optimization. Defaults to False.
        Returns:
            str or generator: Generated response string or generator yielding response chunks.
        """
        if self.logger:
            self.logger.debug(f"Chat request initiated - Prompt: {prompt[:50]}...")

        def for_stream():
            for response in self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(prompt, stream=False, optimizer=optimizer, conversationally=conversationally)
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """
        Retrieves message from the response.

        Args:
            response (dict): Response from the ask() method.
        Returns:
            str: Extracted text.
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    ai = JadveOpenAI(timeout=5000, logging=False)
    # For streaming response demonstration.
    response = ai.chat("yo what's up", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
