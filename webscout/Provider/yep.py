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
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import  Provider, AsyncProvider
from webscout import exceptions
from typing import Any, AsyncGenerator, Dict
import logging
import httpx
import cloudscraper

class YEPCHAT(Provider):
    """
    This class provides methods for interacting with the Yep.com chat API in a consistent provider structure.
    """

    AVAILABLE_MODELS = [
        "Mixtral-8x7B-Instruct-v0.1"  # Add other available models here
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 1280,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "Mixtral-8x7B-Instruct-v0.1",
        temperature: float = 0.6,
        top_p: float = 0.7,
    ):
        """Instantiates YEPCHAT

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 1280.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): Model to use for generating text. Defaults to "Mixtral-8x7B-Instruct-v0.1".
            temperature (float, optional): Temperature parameter for the model. Defaults to 0.6.
            top_p (float, optional): Top_p parameter for the model. Defaults to 0.7.
        """

        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = cloudscraper.create_scraper()  # Create a Cloudscraper session
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://api.yep.com/v1/chat/completions"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'Content-Type': 'application/json; charset=utf-8',
            'DNT': '1',
            'Origin': 'https://yep.com',
            'Referer': 'https://yep.com/',
            'Sec-CH-UA': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
        }
        self.cookies = {
            '__Host-session': uuid4().hex,
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
            stream (bool, optional): Whether to stream the response. Defaults to False.
            raw (bool, optional): Whether to return the raw response. Defaults to False.
            optimizer (str, optional): The name of the optimizer to use. Defaults to None.
            conversationally (bool, optional): Whether to chat conversationally. Defaults to False.

        Returns:
            The response from the API.
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

        data = {
            "stream": stream,
            "max_tokens": self.max_tokens_to_sample,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "messages": [
                {"content": conversation_prompt, "role": "user"}
            ],
            "model": self.model
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, headers=self.headers, cookies=self.cookies, json=data, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason})"
                )
            streaming_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("data: "):
                        json_data = line[6:]
                        if json_data == "[DONE]":
                            break
                        try:
                            data = json.loads(json_data)
                            content = data["choices"][0]["delta"].get("content", "")
                            streaming_response += content
                            yield content if raw else dict(text=streaming_response)
                        except json.decoder.JSONDecodeError:
                            continue
            self.last_response.update(dict(text=streaming_response))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            response = self.session.post(
                self.chat_endpoint, headers=self.headers, cookies=self.cookies, json=data, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason})"
                )
            resp = response.json()
            self.last_response.update(dict(text=resp['choices'][0]['message']['content']))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
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
if __name__ == '__main__':
    from rich import print
    ai = YEPCHAT()
    response = ai.chat("tell me about india")
    for chunk in response:
        print(chunk, end="", flush=True)