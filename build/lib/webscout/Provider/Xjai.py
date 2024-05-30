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
from webscout import exceptions
from typing import Any, AsyncGenerator, Dict
import logging
import httpx
#-----------------------------------------------xjai-------------------------------------------
class Xjai(Provider):
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 0.8,
        top_p: float = 1,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """
        Initializes the Xjai class for interacting with the Xjai AI chat API.

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): The creativity level of the AI's response. Defaults to 0.8.
            top_p (float, optional): The probability threshold for token selection. Defaults to 1.
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
        self.temperature = temperature
        self.top_p = top_p
        self.chat_endpoint = "https://p1api.xjai.pro/freeapi/chat-process"
        self.stream_chunk_size = 1  # Process response line by line
        self.timeout = timeout
        self.last_response = {}

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
    ) -> Any:
        """
        Sends a chat request to the Xjai AI chat API and returns the response.

        Args:
            prompt (str): The query to send to the AI.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.

        Returns:
            Any: The response from the AI, either as a dictionary or a generator 
                 depending on the `stream` and `raw` parameters.
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

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        payload = {
            "prompt": conversation_prompt + "\n\nReply in English Only",
            "systemMessage": "Reply in English Only",
            "temperature": self.temperature,
            "top_p": self.top_p
        }

        def generate_response():
            response = self.session.post(
                self.chat_endpoint, headers=headers, json=payload, stream=True, timeout=self.timeout
            )
            output = ""
            print_next = False

            for line in response.iter_lines(decode_unicode=True, chunk_size=self.stream_chunk_size):
                line_content = line.decode("utf-8")
                # Filter out irrelevant content
                if '[ChatAI](https://srv.aiflarepro.com/#/?cid=4111)' in line_content:
                    continue
                if '&KFw6loC9Qvy&' in line_content:
                    parts = line_content.split('&KFw6loC9Qvy&')
                    if print_next:
                        output += parts[0]
                        print_next = False
                    else:
                        output += parts[1]
                        print_next = True
                        if len(parts) > 2:
                            print_next = False
                elif print_next:
                    output += line_content + '\n'

            # Update chat history
            self.conversation.update_chat_history(prompt, output)

            return output

        def for_stream():
            response = generate_response()
            for line in response.splitlines():
                yield line if raw else dict(text=line)

        def for_non_stream():
            response = generate_response()
            return response if raw else dict(text=response)

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Any:
        """
        Generates a response from the Xjai AI chat API.

        Args:
            prompt (str): The query to send to the AI.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.

        Returns:
            Any: The response from the AI, either as a string or a generator 
                 depending on the `stream` parameter. 
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

    def get_message(self, response: Any) -> str:
        """
        Retrieves the message from the AI's response. 

        Args:
            response (Any): The response from the AI, either a dictionary 
                            or a raw string.

        Returns:
            str: The extracted message from the AI's response. 
        """
        if isinstance(response, dict): 
            return response["text"]
        else:  # Assume raw string
            return response

