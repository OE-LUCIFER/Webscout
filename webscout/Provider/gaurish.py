import requests
import json
from typing import Any, Dict, Generator, Union
import uuid

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from webscout import LitAgent
from webscout.Litlogger import Logger, LogFormat

class GaurishCerebras(Provider):
    """
    A class to interact with the Gaurish Cerebras API with comprehensive logging.
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
        system_prompt: str = "You are a helpful assistant.",
        logging: bool = False
    ):
        """Initializes the Gaurish Cerebras API client with logging capabilities."""
        self.logger = Logger(
            name="GaurishCerebras",
            format=LogFormat.MODERN_EMOJI,
        ) if logging else None

        if self.logger:
            self.logger.info("Initializing GaurishCerebras client")

        self.chat_endpoint = "https://proxy.gaurish.xyz/api/cerebras/v1/chat/completions"

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "authorization": "Bearer 123",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "dnt": "1",
            "origin": "https://chat.gaurish.xyz",
            "priority": "u=1, i",
            "referer": "https://chat.gaurish.xyz/",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"),
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.last_response = {}

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens

        if self.logger:
            self.logger.debug(f"Session configured with timeout: {timeout}")
            self.logger.debug(f"Max tokens set to: {max_tokens}")

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
            else intro or system_prompt or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.system_prompt = system_prompt

        if self.logger:
            self.logger.info("GaurishCerebras initialization completed successfully")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict, Generator]:
        """
        Sends a prompt to the API and returns the response with logging.
        If stream is True, returns a generator for streamed responses.
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
                raise Exception(f"Optimizer is not one of {list(self.__available_optimizers)}")

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "model": "llama3.3-70b",
            "max_tokens": self.max_tokens_to_sample,
            "temperature": 0.75,
            "stream": stream,
        }

        def for_stream():
            try:
                if self.logger:
                    self.logger.debug("Initiating streaming request to API")

                with self.session.post(self.chat_endpoint, json=payload, stream=True, timeout=self.timeout) as response:
                    if response.status_code != 200:
                        if self.logger:
                            self.logger.error(f"API request failed. Status: {response.status_code}")
                        raise exceptions.FailedToGenerateResponseError(
                            f"Request failed with status code {response.status_code}"
                        )

                    if self.logger:
                        self.logger.info(f"API connection established successfully. Status: {response.status_code}")

                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            line = line.strip()
                            if line.startswith("data: "):
                                json_str = line[6:]
                                if json_str == "[DONE]":
                                    if self.logger:
                                        self.logger.debug("Stream completed")
                                    break
                                try:
                                    json_data = json.loads(json_str)
                                    if 'choices' in json_data:
                                        choice = json_data['choices'][0]
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            content = choice['delta']['content']
                                            streaming_text += content
                                            yield dict(text=content) if raw else dict(text=content)
                                except json.JSONDecodeError as e:
                                    if self.logger:
                                        self.logger.error(f"JSON parsing error: {str(e)}")
                                    pass

                    self.conversation.update_chat_history(prompt, streaming_text)
                    if self.logger:
                        self.logger.debug("Response processing completed")

            except requests.RequestException as e:
                if self.logger:
                    self.logger.error(f"Request failed: {str(e)}")
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")

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
    ) -> Union[str, Generator]:
        """
        A convenience method to return just the text message from the response with logging.
        """
        if self.logger:
            self.logger.debug(f"Chat request initiated - Prompt: {prompt[:50]}...")

        def for_stream():
            for response in self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            ):
                yield response if isinstance(response, str) else self.get_message(response)

        def for_non_stream():
            resp = self.ask(
                prompt, stream=False, optimizer=optimizer, conversationally=conversationally
            )
            return resp if isinstance(resp, str) else self.get_message(resp)

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """
        Retrieve the message text from the API response with logging.
        """
        if not isinstance(response, dict):
            if self.logger:
                self.logger.warning("Invalid response format received")
            return ""

        if "text" in response and response["text"]:
            return response["text"]

        if self.logger:
            self.logger.warning("No valid message content found in response")
        return ""

if __name__ == "__main__":
    from rich import print
    bot = GaurishCerebras(logging=True)
    try:
        response = bot.chat("what is meaning of life", stream=True)
        for chunk in response:
            print(chunk, end="", flush=True)
    except Exception as e:
        print(f"An error occurred: {e}")
