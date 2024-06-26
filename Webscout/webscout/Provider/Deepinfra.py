import time
import uuid
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
from ..AIbase import Provider, AsyncProvider
from webscout import exceptions
from typing import Any, AsyncGenerator
import logging
import httpx

class DeepInfra(Provider):
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
        model: str = "Qwen/Qwen2-72B-Instruct",
        system_prompt: str = "You are a Helpful AI."
    ):
        """Instantiates DeepInfra

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): DeepInfra model name. Defaults to "meta-llama/Meta-Llama-3-70B-Instruct".
            system_prompt (str, optional): System prompt for DeepInfra. Defaults to "You are a Helpful AI.".
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://deepinfra.com',
            'Pragma': 'no-cache',
            'Referer': 'https://deepinfra.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'X-Deepinfra-Source': 'web-embed',
            'accept': 'text/event-stream',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
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
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with AI

        Args:
        prompt (str): Prompt to be sent.
        raw (bool, optional): Stream back raw response as received. Defaults to False.
        optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
        conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
        dict : {}
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
            'model': self.model,
            'messages': [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            'temperature': 0.7,
            'max_tokens': 8028,
            'stop': []
        }

        response = self.session.post(
            self.chat_endpoint, json=payload, timeout=self.timeout
        )
        if not response.ok:
            raise Exception(
                f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
            )

        resp = response.json()
        message_load = self.get_message(resp)
        self.conversation.update_chat_history(
            prompt, message_load
        )
        return resp

    def chat(
        self,
        prompt: str,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
        """
        return self.get_message(
            self.ask(
                prompt,
                optimizer=optimizer,
                conversationally=conversationally,
            )
        )

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        try:
            return response["choices"][0]["message"]["content"]
        except KeyError:
            return ""

class AsyncDeepInfra(AsyncProvider):
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
        model: str = "meta-llama/Meta-Llama-3-70B-Instruct",
        system_prompt: str = "You are a Helpful AI."
    ):
        """Instantiates DeepInfra

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): DeepInfra model name. Defaults to "meta-llama/Meta-Llama-3-70B-Instruct".
            system_prompt (str, optional): System prompt for DeepInfra. Defaults to "You are a Helpful AI.".
        """
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://deepinfra.com',
            'Pragma': 'no-cache',
            'Referer': 'https://deepinfra.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'X-Deepinfra-Source': 'web-embed',
            'accept': 'text/event-stream',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.client = httpx.AsyncClient(proxies=proxies, headers=self.headers)
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

    async def ask(
        self,
        prompt: str,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with AI

        Args:
        prompt (str): Prompt to be sent.
        raw (bool, optional): Stream back raw response as received. Defaults to False.
        optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
        conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
        dict : {}
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
            'model': self.model,
            'messages': [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            'temperature': 0.7,
            'max_tokens': 8028,
            'stop': []
        }

        response = await self.client.post(self.chat_endpoint, json=payload, timeout=self.timeout)
        if response.status_code != 200:
            raise Exception(
                f"Failed to generate response - ({response.status_code}, {response.reason_phrase}) - {response.text}"
            )

        resp = response.json()
        message_load = self.get_message(resp)
        self.conversation.update_chat_history(
            prompt, message_load
        )
        return resp

    async def chat(
        self,
        prompt: str,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
        """
        return self.get_message(
            await self.ask(
                prompt,
                optimizer=optimizer,
                conversationally=conversationally,
            )
        )

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        try:
            return response["choices"][0]["message"]["content"]
        except KeyError:
            return ""
import requests
import base64
from typing import List, Dict, Union, Any

class VLM:
    def __init__(
        self,
        model: str = "llava-hf/llava-1.5-7b-hf",
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        system_prompt: str = "You are a Helpful AI.",
        proxies: dict = {}
    ):
        """Instantiates VLM

        Args:
            model (str): VLM model name.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            system_prompt (str, optional): System prompt for VLM. Defaults to "You are a Helpful AI.".
            proxies (dict, optional): Http request proxies. Defaults to {}.
        """
        self.model = model
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.system_prompt = system_prompt
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q.0.7,es;q.0.6,en-US;q.0.5,am;q.0.4,de;q.0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://deepinfra.com',
            'Pragma': 'no-cache',
            'Referer': 'https://deepinfra.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'X-Deepinfra-Source': 'web-embed',
            'accept': 'text/event-stream',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

    def encode_image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        try:
            return response["choices"][0]["message"]["content"]
        except KeyError:
            return ""

    def ask(
        self,
        prompt: Union[str, Dict[str, str]],
        raw: bool = False
    ) -> dict:
        """Chat with AI

        Args:
            prompt (Union[str, Dict[str, str]]): Prompt to be sent, can be text or a dict with base64 image.
            raw (bool, optional): Stream back raw response as received. Defaults to False.

        Returns:
            dict: Response from the API
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt if isinstance(prompt, str) else prompt['content']}
        ]

        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': self.max_tokens_to_sample,
            'stop': [],
            'stream': False
        }

        response = self.session.post(
            "https://api.deepinfra.com/v1/openai/chat/completions",
            json=payload,
            timeout=self.timeout
        )
        if not response.ok:
            raise Exception(
                f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
            )

        return response.json()

    def chat(
        self,
        prompt: Union[str, Dict[str, str]]
    ) -> str:
        """Generate response `str`

        Args:
            prompt (Union[str, Dict[str, str]]): Prompt to be sent, can be text or a dict with base64 image.

        Returns:
            str: Response generated
        """
        return self.get_message(self.ask(prompt))