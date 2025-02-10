import requests
import re
import json
from typing import Any, Dict, Generator, Optional

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme

class DGAFAI(Provider):
    """
    A class to interact with the DGAF.ai API with logging capabilities.
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
        system_prompt: str = "You are a helpful AI assistant.",
        logging: bool = False
    ):
        """Initializes the DGAFAI API client with logging support."""
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://www.dgaf.ai/api/chat"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt

        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "cookie": "_ga=GA1.1.1717609725.1738729535; _ga_52CD0XKYNM=GS1.1.1738729535.1.0.1738729546.0.0.0",
            "dnt": "1",
            "origin": "https://www.dgaf.ai",
            "referer": "https://www.dgaf.ai/?via=topaitools",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": LitAgent().random(),
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

        # Initialize logger if enabled
        self.logger = LitLogger(
            name="DGAFAI",
            format=LogFormat.MODERN_EMOJI,
            color_scheme=ColorScheme.CYBERPUNK
        ) if logging else None

        if self.logger:
            self.logger.info("DGAFAI initialized successfully")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator[str, None, None]:
        """Chat with AI.
        
        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Return raw streaming response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            Union[Dict, Generator[Dict, None, None]]: Generated response.
        """
        if self.logger:
            self.logger.debug(f"Processing ask call with prompt: {prompt[:50]}...")
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
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ]
        }

        def for_stream():
            if self.logger:
                self.logger.debug("Sending streaming request to DGAF.ai API...")
            try:
                with self.session.post(self.api_endpoint, headers=self.headers, json=payload, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()  # Check for HTTP errors
                    if self.logger:
                        self.logger.debug(response.text)
                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            match = re.search(r'0:"(.*?)"', line)
                            if match:
                                content = match.group(1)
                                if content:
                                    streaming_text += content
                                    # if self.logger:
                                    #     self.logger.debug(f"Received content: {content[:30]}...")
                                    yield content if raw else dict(text=content)
                    self.last_response.update(dict(text=streaming_text))
                    self.conversation.update_chat_history(
                        prompt, self.get_message(self.last_response)
                    )
                    if self.logger:
                        self.logger.info("Streaming response completed successfully")
            except requests.exceptions.RequestException as e:
                if self.logger:
                    self.logger.error(f"Request error: {e}")
                raise exceptions.ProviderConnectionError(f"Request failed: {e}")

        def for_non_stream():
            full_response = ""
            for chunk in for_stream():
                full_response += chunk if raw else chunk['text']
            return {"text": full_response}

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:
        """Generate chat response as a string.
        
        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Use conversational mode when using optimizer. Defaults to False.
        Returns:
            str or Generator[str, None, None]: Generated response.
        """
        if self.logger:
            self.logger.debug(f"Chat method invoked with prompt: {prompt[:50]}...")
        def for_stream():
            for response in self.ask(prompt, True, optimizer=optimizer, conversationally=conversationally):
                yield self.get_message(response)
        def for_non_stream():
            return self.get_message(
                self.ask(prompt, False, optimizer=optimizer, conversationally=conversationally)
            )
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response.
        
        Args:
            response (dict): Response from the ask method.
        Returns:
            str: Extracted message.
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')


if __name__ == "__main__":
    from rich import print
    ai = DGAFAI(logging=False)
    response = ai.chat("write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
