import requests
import json
from typing import Any, Dict, Generator, Optional

from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.Litlogger import Logger, LogFormat
from webscout import LitAgent as Lit

class GliderAI(Provider):
    """
    A class to interact with the Glider.so API with comprehensive logging.
    """

    AVAILABLE_MODELS = {
        "chat-llama-3-1-70b",
        "chat-llama-3-1-8b",
        "chat-llama-3-2-3b",
        "deepseek-ai/DeepSeek-R1",
    }

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "chat-llama-3-1-70b",
        system_prompt: str = "You are a helpful AI assistant.",
        logging: bool = False
    ):
        """Initializes the GliderAI API client with logging capabilities."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {', '.join(self.AVAILABLE_MODELS)}")
        
        self.logger = Logger(
            name="GliderAI",
            format=LogFormat.MODERN_EMOJI,

        ) if logging else None

        if self.logger:
            self.logger.info(f"Initializing GliderAI with model: {model}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://glider.so/api/chat"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://glider.so",
            "referer": "https://glider.so/",
            "user-agent": Lit().random(),
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
            self.logger.info("GliderAI initialized successfully")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """Chat with AI with logging capabilities.

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Return raw response chunks instead of dict. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Use conversationally modified prompt when optimizer specified. Defaults to False.
        Returns:
            dict or Generator[dict, None, None]: The response from the API.
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
                {"role": "user", "content": conversation_prompt},
                {"role": "system", "content": self.system_prompt}
            ],
            "model": self.model,
        }

        def for_stream():
            if self.logger:
                self.logger.debug("Initiating streaming request to API")
            response = self.session.post(
                self.api_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                if self.logger:
                    self.logger.error(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )
            streaming_text = ""
            for value in response.iter_lines(decode_unicode=True):
                if value:
                    if value.startswith("data: "):
                        try:
                            data = json.loads(value[6:])
                            content = data['choices'][0].get('delta', {}).get("content", "")
                            if content:
                                streaming_text += content
                                yield content if raw else {"text": content}
                        except json.JSONDecodeError:
                            if "stop" in value:
                                break
            self.last_response.update(dict(text=streaming_text))
            self.conversation.update_chat_history(prompt, self.get_message(self.last_response))
            if self.logger:
                self.logger.debug("Response processing completed")

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
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:
        """Generate response as a string with logging.

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Use conversationally modified prompt when optimizer specified. Defaults to False.
        Returns:
            str or Generator[str, None, None]: The response generated.
        """
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

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response."""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    # For testing with logging enabled
    ai = GliderAI(model="chat-llama-3-1-70b", logging=True)
    response = ai.chat("Meaning of Life", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)