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
from typing import Any, AsyncGenerator, Dict
import logging
import httpx
#--------------------------------------LEO-----------------------------------------
class LEO(Provider):
    
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 0.2,
        top_k: int = -1,
        top_p: float = 0.999,
        model: str = "llama-2-13b-chat",
        brave_key: str = "qztbjzBqJueQZLFkwTTJrieu8Vw3789u",
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Instantiate TGPT

        Args:
            is_conversation (str, optional): Flag for chatting conversationally. Defaults to True.
            brave_key (str, optional): Brave API access key. Defaults to "qztbjzBqJueQZLFkwTTJrieu8Vw3789u".
            model (str, optional): Text generation model name. Defaults to "llama-2-13b-chat".
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 0.2.
            top_k (int, optional): Chance of topic being repeated. Defaults to -1.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 0.999.
            timeput (int, optional): Http requesting timeout. Defaults to 30
            intro (str, optional): Conversation introductory prompt. Defaults to `Conversation.intro`.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional) : Http reqiuest proxies (socks). Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.model = model
        self.stop_sequences = ["</response>", "</s>"]
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.chat_endpoint = "https://ai-chat.bsg.brave.com/v1/complete"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Content-Type": "application/json",
            "accept": "text/event-stream",
            "x-brave-key": brave_key,
            "accept-language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/110.0",
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
        self.system_prompt = (
            "\n\nYour name is Leo, a helpful"
            "respectful and honest AI assistant created by the company Brave. You will be replying to a user of the Brave browser. "
            "Always respond in a neutral tone. Be polite and courteous. Answer concisely in no more than 50-80 words."
            "\n\nPlease ensure that your responses are socially unbiased and positive in nature."
            "If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. "
            "If you don't know the answer to a question, please don't share false information.\n"
        )

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
            "completion": "\nNext: domestic cat breeds with short hair >>",
            "stop_reason": null,
            "truncated": false,
            "stop": null,
            "model": "llama-2-13b-chat",
            "log_id": "cmpl-3kYiYxSNDvgMShSzFooz6t",
            "exception": null
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

        self.session.headers.update(self.headers)
        payload = {
            "max_tokens_to_sample": self.max_tokens_to_sample,
            "model": self.model,
            "prompt": f"<s>[INST] <<SYS>>{self.system_prompt}<</SYS>>{conversation_prompt} [/INST]",
            "self.stop_sequence": self.stop_sequences,
            "stream": stream,
            "top_k": self.top_k,
            "top_p": self.top_p,
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if (
                not response.ok
                or not response.headers.get("Content-Type")
                == "text/event-stream; charset=utf-8"
            ):
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            for value in response.iter_lines(
                decode_unicode=True,
                delimiter="" if raw else "data:",
                chunk_size=self.stream_chunk_size,
            ):
                try:
                    resp = json.loads(value)
                    self.last_response.update(resp)
                    yield value if raw else resp
                except json.decoder.JSONDecodeError:
                    pass
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=False, timeout=self.timeout
            )
            if (
                not response.ok
                or not response.headers.get("Content-Type", "") == "application/json"
            ):
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )
            resp = response.json()
            self.last_response.update(resp)
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            return resp

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
        return response.get("completion")
class AsyncLEO(AsyncProvider):
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 0.2,
        top_k: int = -1,
        top_p: float = 0.999,
        model: str = "llama-2-13b-chat",
        brave_key: str = "qztbjzBqJueQZLFkwTTJrieu8Vw3789u",
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Instantiate TGPT

        Args:
            is_conversation (str, optional): Flag for chatting conversationally. Defaults to True.
            brave_key (str, optional): Brave API access key. Defaults to "qztbjzBqJueQZLFkwTTJrieu8Vw3789u".
            model (str, optional): Text generation model name. Defaults to "llama-2-13b-chat".
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 0.2.
            top_k (int, optional): Chance of topic being repeated. Defaults to -1.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 0.999.
            timeput (int, optional): Http requesting timeout. Defaults to 30
            intro (str, optional): Conversation introductory prompt. Defaults to `Conversation.intro`.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional) : Http reqiuest proxies (socks). Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.model = model
        self.stop_sequences = ["</response>", "</s>"]
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.chat_endpoint = "https://ai-chat.bsg.brave.com/v1/complete"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Content-Type": "application/json",
            "accept": "text/event-stream",
            "x-brave-key": brave_key,
            "accept-language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/110.0",
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
        self.system_prompt = (
            "\n\nYour name is Leo, a helpful"
            "respectful and honest AI assistant created by the company Brave. You will be replying to a user of the Brave browser. "
            "Always respond in a neutral tone. Be polite and courteous. Answer concisely in no more than 50-80 words."
            "\n\nPlease ensure that your responses are socially unbiased and positive in nature."
            "If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. "
            "If you don't know the answer to a question, please don't share false information.\n"
        )
        self.session = httpx.AsyncClient(headers=self.headers, proxies=proxies)

    async def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict | AsyncGenerator:
        """Chat with AI asynchronously.

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
           dict|AsyncGenerator : ai content
        ```json
        {
            "completion": "\nNext: domestic cat breeds with short hair >>",
            "stop_reason": null,
            "truncated": false,
            "stop": null,
            "model": "llama-2-13b-chat",
            "log_id": "cmpl-3kYiYxSNDvgMShSzFooz6t",
            "exception": null
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

        payload = {
            "max_tokens_to_sample": self.max_tokens_to_sample,
            "model": self.model,
            "prompt": f"<s>[INST] <<SYS>>{self.system_prompt}<</SYS>>{conversation_prompt} [/INST]",
            "self.stop_sequence": self.stop_sequences,
            "stream": stream,
            "top_k": self.top_k,
            "top_p": self.top_p,
        }

        async def for_stream():
            async with self.session.stream(
                "POST", self.chat_endpoint, json=payload, timeout=self.timeout
            ) as response:
                if (
                    not response.is_success
                    or not response.headers.get("Content-Type")
                    == "text/event-stream; charset=utf-8"
                ):
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason_phrase})"
                    )
                async for value in response.aiter_lines():
                    try:
                        resp = sanitize_stream(value)
                        self.last_response.update(resp)
                        yield value if raw else resp
                    except json.decoder.JSONDecodeError:
                        pass

            self.conversation.update_chat_history(
                prompt, await self.get_message(self.last_response)
            )

        async def for_non_stream():
            async for _ in for_stream():
                pass
            return self.last_response

        return for_stream() if stream else await for_non_stream()

    async def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | AsyncGenerator:
        """Generate response `str` asynchronously.
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str|AsyncGenerator: Response generated
        """

        async def for_stream():
            async_ask = await self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            )
            async for response in async_ask:
                yield await self.get_message(response)

        async def for_non_stream():
            return await self.get_message(
                await self.ask(
                    prompt,
                    False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
            )

        return for_stream() if stream else await for_non_stream()

    async def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response.get("completion")