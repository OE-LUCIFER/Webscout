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

#-------------------------------------------------------yep.com--------------------------------------------------------   
class YEPCHAT(Provider):
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 0.6,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 0.7,
        model: str = "Mixtral-8x7B-Instruct-v0.1",
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Instantiates YEPCHAT

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 0.6.
            presence_penalty (int, optional): Chances of topic being repeated. Defaults to 0.
            frequency_penalty (int, optional): Chances of word being repeated. Defaults to 0.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 0.7.
            model (str, optional): LLM model name. Defaults to "gpt-3.5-turbo".
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p
        self.chat_endpoint = "https://api.yep.com/v1/chat/completions"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json; charset=utf-8",
            "Origin": "https://yep.com",
            "Referer": "https://yep.com/",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
            "id": "cmpl-c61c1c88de4e4ad3a79134775d17ea0c",
            "object": "chat.completion.chunk",
            "created": 1713876886,
            "model": "Mixtral-8x7B-Instruct-v0.1",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "role": null,
                        "content": " Sure, I can help with that. Are you looking for information on how to start coding, or do you need help with a specific coding problem? We can discuss various programming languages like Python, JavaScript, Java, C++, or others. Please provide more details so I can assist you better."
                        },
                    "finish_reason": null
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
        self.session.headers.update(self.headers)
        payload = {
            "stream": True,
            "max_tokens": 1280,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "messages": [{"content": conversation_prompt, "role": "user"}],
            "model": self.model,
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            message_load = ""
            for value in response.iter_lines(
                decode_unicode=True,
                delimiter="" if raw else "data:",
                chunk_size=self.stream_chunk_size,
            ):
                try:
                    resp = json.loads(value)
                    incomplete_message = self.get_message(resp)
                    if incomplete_message:
                        message_load += incomplete_message
                        resp["choices"][0]["delta"]["content"] = message_load
                        self.last_response.update(resp)
                        yield value if raw else resp
                    elif raw:
                        yield value
                except json.decoder.JSONDecodeError:
                    pass
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

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
        try:
            if response["choices"][0].get("delta"):
                return response["choices"][0]["delta"]["content"]
            return response["choices"][0]["message"]["content"]
        except KeyError:
            return ""
class AsyncYEPCHAT(AsyncProvider):
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 0.6,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 0.7,
        model: str = "Mixtral-8x7B-Instruct-v0.1",
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Instantiates YEPCHAT

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 0.6.
            presence_penalty (int, optional): Chances of topic being repeated. Defaults to 0.
            frequency_penalty (int, optional): Chances of word being repeated. Defaults to 0.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 0.7.
            model (str, optional): LLM model name. Defaults to "gpt-3.5-turbo".
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p
        self.chat_endpoint = "https://api.yep.com/v1/chat/completions"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json; charset=utf-8",
            "Origin": "https://yep.com",
            "Referer": "https://yep.com/",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
        self.session = httpx.AsyncClient(
            headers=self.headers,
            proxies=proxies,
        )

    async def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with AI asynchronously.

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
            "id": "cmpl-c61c1c88de4e4ad3a79134775d17ea0c",
            "object": "chat.completion.chunk",
            "created": 1713876886,
            "model": "Mixtral-8x7B-Instruct-v0.1",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "role": null,
                        "content": " Sure, I can help with that. Are you looking for information on how to start coding, or do you need help with a specific coding problem? We can discuss various programming languages like Python, JavaScript, Java, C++, or others. Please provide more details so I can assist you better."
                        },
                    "finish_reason": null
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
        payload = {
            "stream": True,
            "max_tokens": 1280,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "messages": [{"content": conversation_prompt, "role": "user"}],
            "model": self.model,
        }

        async def for_stream():
            async with self.session.stream(
                "POST", self.chat_endpoint, json=payload, timeout=self.timeout
            ) as response:
                if not response.is_success:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason_phrase}) - {response.text}"
                    )

                message_load = ""
                async for value in response.aiter_lines():
                    try:
                        resp = sanitize_stream(value)
                        incomplete_message = await self.get_message(resp)
                        if incomplete_message:
                            message_load += incomplete_message
                            resp["choices"][0]["delta"]["content"] = message_load
                            self.last_response.update(resp)
                            yield value if raw else resp
                        elif raw:
                            yield value
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
    ) -> str:
        """Generate response `str` asynchronously.
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
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
        try:
            if response["choices"][0].get("delta"):
                return response["choices"][0]["delta"]["content"]
            return response["choices"][0]["message"]["content"]
        except KeyError:
            return ""