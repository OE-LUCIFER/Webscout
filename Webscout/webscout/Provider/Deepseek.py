import time
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import click
import requests
from requests import get
from uuid import uuid4
from re import findall
from requests.exceptions import RequestException
from curl_cffi.requests import get, RequestsError
import g4f
from random import randint
from PIL import Image
import io
import re
import json
import yaml
from ..AIutel import Optimizers
from ..AIutel import Conversation
from ..AIutel import AwesomePrompts, sanitize_stream
from ..AIbase import  Provider, AsyncProvider
from Helpingai_T2 import Perplexity
from webscout import exceptions
from typing import Any, AsyncGenerator, Dict, Optional
import logging
import httpx
import os
from dotenv import load_dotenv; load_dotenv()

#-----------------------------------------------DeepSeek--------------------------------------------
class DeepSeek(Provider):
    def __init__(
        self,
        api_key: str,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = 'deepseek_chat',
        temperature: float = 1.0,
    ):
        """Initializes DeepSeek

        Args:
            api_key (str): DeepSeek API key.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model_type (str, optional): DeepSeek model type. Defaults to 'deepseek_chat'.
            temperature (float, optional): Creativity level of the response. Defaults to 1.0.
        """
        self.api_token = api_key
        self.auth_headers = {
            'Authorization': f'Bearer {self.api_token}'
        }
        self.api_base_url = 'https://chat.deepseek.com/api/v0/chat'
        self.api_session = requests.Session()
        self.api_session.headers.update(self.auth_headers)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model_type = model
        self.temperature = temperature
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
        # self.session.proxies = proxies

    def clear_chat(self) -> None:
        """
        Clears the chat context by making a POST request to the clear_context endpoint.
        """
        clear_payload = {"model_class": "deepseek_chat", "append_welcome_message": False}
        clear_response = self.api_session.post(f'{self.api_base_url}/clear_context', json=clear_payload)
        clear_response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code

    def generate(self, user_message: str, response_temperature: float = 1.0, model_type: Optional[str] = "deepseek_chat", verbose: bool = False) -> str:
        """
        Generates a response from the DeepSeek API based on the provided message.

        Args:
            user_message (str): The message to send to the chat API.
            response_temperature (float, optional): The creativity level of the response. Defaults to 1.0.
            model_type (str, optional): The model class to be used for the chat session.
            verbose (bool, optional): Whether to print the response content. Defaults to False.

        Returns:
            str: The concatenated response content received from the API.

        Available models:
            - deepseek_chat
            - deepseek_code
        """
        request_payload = {
            "message": user_message,
            "stream": True,
            "model_preference": None,
            "model_class": model_type,
            "temperature": response_temperature
        }
        api_response = self.api_session.post(f'{self.api_base_url}/completions', json=request_payload, stream=True)
        api_response.raise_for_status()

        combined_response = ""
        for response_line in api_response.iter_lines(decode_unicode=True, chunk_size=1):
            if response_line:
                cleaned_line = re.sub("data:", "", response_line)
                response_json = json.loads(cleaned_line)
                response_content = response_json['choices'][0]['delta']['content']
                if response_content and not re.match(r'^\s{5,}$', response_content):
                    if verbose: print(response_content, end="", flush=True)
                    combined_response += response_content

        return combined_response

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with AI

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
           dict : {}
        ```json
        {
            "id": "chatcmpl-TaREJpBZsRVQFRFic1wIA7Q7XfnaD",
            "object": "chat.completion",
            "created": 1704623244,
            "model": "gpt-3.5-turbo",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
                },
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I assist you today?"
                },
                "finish_reason": "stop",
                "index": 0
                }
            ]
        }
        ```
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        def for_stream():
            response = self.generate(
                user_message=conversation_prompt,
                response_temperature=self.temperature,
                model_type=self.model_type,
                verbose=False,
            )
            # print(response)
            self.last_response.update(dict(text=response))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            yield dict(text=response) if raw else dict(text=response)

        def for_non_stream():
            # let's make use of stream
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
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
        """

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
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]