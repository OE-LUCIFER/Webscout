import requests
import json
import time
from typing import Any, Dict, Optional, Generator, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from webscout import LitAgent
from webscout.Litlogger import Logger, LogFormat

class FreeAIChat(Provider):
    """
    A class to interact with the FreeAIChat API with logging and LitAgent user-agent.
    """

    AVAILABLE_MODELS = [
        "mistral-nemo",
        "mistral-large",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2.0-pro-exp-02-05",
        "deepseek-r1",
        "deepseek-v3",
        "Deepseek r1 14B",
        "Deepseek r1 32B",
        "o3-mini-high",
        "o3-mini-medium",
        "o3-mini-low",
        "o3-mini",
        "GPT-4o-mini",
        "o1",
        "o1-mini",
        "GPT-4o",
        "Qwen coder",
        "Qwen 2.5 72B",
        "Llama 3.1 405B",
        "llama3.1-70b-fast",
        "Llama 3.3 70B",
        "claude 3.5 haiku",
        "claude 3.5 sonnet",
    ]

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
        model: str = "GPT-4o",
        system_prompt: str = "You are a helpful AI assistant.",
        logging: bool = False
    ):
        """Initializes the FreeAIChat API client with logging support."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.url = "https://freeaichatplayground.com/api/v1/chat/completions"
        self.headers = {
            'User-Agent': LitAgent().random(),
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'Origin': 'https://freeaichatplayground.com',
            'Referer': 'https://freeaichatplayground.com/',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt

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

        self.logger = Logger(
            name="FreeAIChat",
            format=LogFormat.MODERN_EMOJI,
        ) if logging else None

        if self.logger:
            self.logger.info(f"FreeAIChat initialized successfully with model: {model}")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
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
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": conversation_prompt
            }
        ]

        payload = {
            "model": self.model,
            "messages": messages
        }

        def for_stream():
            if self.logger:
                self.logger.debug("Sending streaming request to FreeAIChat API...")
            try:
                with requests.post(self.url, headers=self.headers, json=payload, stream=True, timeout=self.timeout) as response:
                    if response.status_code != 200:
                        if self.logger:
                            self.logger.error(f"Request failed with status code {response.status_code}")
                        raise exceptions.FailedToGenerateResponseError(
                            f"Request failed with status code {response.status_code}"
                        )
                    
                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            line = line.strip()
                            if line.startswith("data: "):
                                json_str = line[6:]  # Remove "data: " prefix
                                if json_str == "[DONE]":
                                    break
                                try:
                                    json_data = json.loads(json_str)
                                    if 'choices' in json_data:
                                        choice = json_data['choices'][0]
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            content = choice['delta']['content']
                                            streaming_text += content
                                            resp = dict(text=content)
                                            yield resp if raw else resp
                                except json.JSONDecodeError:
                                    if self.logger:
                                        self.logger.error("JSON decode error in streaming data")
                                    pass
                    
                    self.conversation.update_chat_history(prompt, streaming_text)
                    if self.logger:
                        self.logger.info("Streaming response completed successfully")
                        
            except requests.RequestException as e:
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
        def for_stream():
            for response in self.ask(prompt, True, optimizer=optimizer, conversationally=conversationally):
                yield self.get_message(response)
                
        def for_non_stream():
            return self.get_message(
                self.ask(prompt, False, optimizer=optimizer, conversationally=conversationally)
            )
            
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    ai = FreeAIChat(model="GPT-4o", logging=True)
    response = ai.chat("Write a hello world program in Python", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)