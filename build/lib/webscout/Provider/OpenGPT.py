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
#------------------------------------------------------OpenGPT-----------------------------------------------------------
class OPENGPT:
    def __init__(
        self,
        assistant_id,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Instantiates OPENGPT

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.session = requests.Session()
        self.max_tokens_to_sample = max_tokens
        self.is_conversation = is_conversation
        self.chat_endpoint = (
            "https://opengpts-example-vz4y4ooboq-uc.a.run.app/runs/stream"
        )
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.assistant_id = assistant_id
        self.authority = "opengpts-example-vz4y4ooboq-uc.a.run.app"

        self.headers = {
            "authority": self.authority,
            "accept": "text/event-stream",
            "accept-language": "en-US,en;q=0.7",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://opengpts-example-vz4y4ooboq-uc.a.run.app",
            "pragma": "no-cache",
            "referer": "https://opengpts-example-vz4y4ooboq-uc.a.run.app/",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
            "messages": [
                {
                    "content": "Hello there",
                    "additional_kwargs": {},
                    "type": "human",
                    "example": false
                },
                {
                    "content": "Hello! How can I assist you today?",
                    "additional_kwargs": {
                    "agent": {
                        "return_values": {
                            "output": "Hello! How can I assist you today?"
                            },
                        "log": "Hello! How can I assist you today?",
                        "type": "AgentFinish"
                    }
                },
                "type": "ai",
                "example": false
                }]
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
        self.session.headers.update(
            dict(
                cookie=f"opengpts_user_id={uuid4().__str__()}",
            )
        )
        payload = {
            "input": [
                {
                    "content": conversation_prompt,
                    "additional_kwargs": {},
                    "type": "human",
                    "example": False,
                },
            ],
            "assistant_id": self.assistant_id,
            "thread_id": "",
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
                chunk_size=self.stream_chunk_size,
            ):
                try:
                    modified_value = re.sub("data:", "", value)
                    resp = json.loads(modified_value)
                    if len(resp) == 1:
                        continue
                    self.last_response.update(resp[1])
                    yield value if raw else resp[1]
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
        return response["content"]
class AsyncOPENGPT(AsyncProvider):
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
    ):
        """Instantiates OPENGPT

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.max_tokens_to_sample = max_tokens
        self.is_conversation = is_conversation
        self.chat_endpoint = (
            "https://opengpts-example-vz4y4ooboq-uc.a.run.app/runs/stream"
        )
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.assistant_id = "bca37014-6f97-4f2b-8928-81ea8d478d88"
        self.authority = "opengpts-example-vz4y4ooboq-uc.a.run.app"

        self.headers = {
            "authority": self.authority,
            "accept": "text/event-stream",
            "accept-language": "en-US,en;q=0.7",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://opengpts-example-vz4y4ooboq-uc.a.run.app",
            "pragma": "no-cache",
            "referer": "https://opengpts-example-vz4y4ooboq-uc.a.run.app/",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
        self.session = httpx.AsyncClient(headers=self.headers, proxies=proxies)

    async def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict | AsyncGenerator:
        """Chat with AI asynchronously

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
           dict|AsyncGenerator : ai content.
        ```json
        {
            "messages": [
                {
                    "content": "Hello there",
                    "additional_kwargs": {},
                    "type": "human",
                    "example": false
                },
                {
                    "content": "Hello! How can I assist you today?",
                    "additional_kwargs": {
                    "agent": {
                        "return_values": {
                            "output": "Hello! How can I assist you today?"
                            },
                        "log": "Hello! How can I assist you today?",
                        "type": "AgentFinish"
                    }
                },
                "type": "ai",
                "example": false
                }]
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
        self.headers.update(
            dict(
                cookie=f"opengpts_user_id={uuid4().__str__()}",
            )
        )
        payload = {
            "input": [
                {
                    "content": conversation_prompt,
                    "additional_kwargs": {},
                    "type": "human",
                    "example": False,
                },
            ],
            "assistant_id": self.assistant_id,
            "thread_id": "",
        }

        async def for_stream():
            async with self.session.stream(
                "POST",
                self.chat_endpoint,
                json=payload,
                timeout=self.timeout,
                headers=self.headers,
            ) as response:
                if (
                    not response.is_success
                    or not response.headers.get("Content-Type")
                    == "text/event-stream; charset=utf-8"
                ):
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason_phrase}) - {response.text}"
                    )

                async for value in response.aiter_lines():
                    try:
                        modified_value = re.sub("data:", "", value)
                        resp = json.loads(modified_value)
                        if len(resp) == 1:
                            continue
                        self.last_response.update(resp[1])
                        yield value if raw else resp[1]
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
        return response["content"]