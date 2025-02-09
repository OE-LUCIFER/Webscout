
import requests
import json
from typing import Any, Dict, Optional, Generator, List

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout import LitAgent as Lit

class LLMChat(Provider):
    """
    A class to interact with the LLMChat API with comprehensive logging.
    """

    AVAILABLE_MODELS = [
        "@cf/meta/llama-3.1-70b-instruct",
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/meta/llama-3.2-3b-instruct",
        "@cf/meta/llama-3.2-1b-instruct"
        "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
        "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
    ]

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
        model: str = "@cf/meta/llama-3.1-70b-instruct",
        system_prompt: str = "You are a helpful assistant.",
        logging: bool = False
    ):
        """
        Initializes the LLMChat API with given parameters and logging capabilities.
        """
        self.logger = LitLogger(
            name="LLMChat",
            format=LogFormat.MODERN_EMOJI,
            color_scheme=ColorScheme.CYBERPUNK
        ) if logging else None

        if self.logger:
            self.logger.info(f"Initializing LLMChat with model: {model}")

        if model not in self.AVAILABLE_MODELS:
            if self.logger:
                self.logger.error(f"Invalid model selected: {model}")
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://llmchat.in/inference/stream"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": Lit().random(),
            "Origin": "https://llmchat.in",
            "Referer": "https://llmchat.in/"
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
            self.logger.info("LLMChat initialized successfully")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        """Chat with LLMChat with logging capabilities"""
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

        url = f"{self.api_endpoint}?model={self.model}"
        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ],
            "max_tokens": self.max_tokens_to_sample,
            "stream": stream
        }

        def for_stream():
            try:
                if self.logger:
                    self.logger.debug("Initiating streaming request to API")

                with requests.post(url, json=payload, headers=self.headers, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()
                    
                    if self.logger:
                        self.logger.info(f"API connection established successfully. Status: {response.status_code}")

                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                try:
                                    data = json.loads(line[6:])
                                    if data.get('response'):
                                        response_text = data['response']
                                        full_response += response_text
                                        yield response_text if raw else dict(text=response_text)
                                except json.JSONDecodeError:
                                    if line.strip() != 'data: [DONE]':
                                        if self.logger:
                                            self.logger.warning(f"Failed to parse line: {line}")
                                    continue

                    self.last_response.update(dict(text=full_response))
                    self.conversation.update_chat_history(
                        prompt, self.get_message(self.last_response)
                    )

            except requests.exceptions.RequestException as e:
                if self.logger:
                    self.logger.error(f"API request failed: {str(e)}")
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")
        
        def for_non_stream():
            if self.logger:
                self.logger.debug("Processing non-streaming request")
            
            full_response = ""
            for line in for_stream():
                full_response += line['text'] if not raw else line
            
            if self.logger:
                self.logger.debug("Response processing completed")
            
            return dict(text=full_response)

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:
        """Generate response with logging capabilities"""
        if self.logger:
            self.logger.debug(f"Chat request initiated - Prompt: {prompt[:50]}...")

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

    def get_message(self, response: Dict[str, Any]) -> str:
        """Retrieves message from response with validation"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    # Enable logging for testing
    ai = LLMChat(model='@cf/meta/llama-3.1-70b-instruct', logging=True)
    response = ai.chat("What's the meaning of life?", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
