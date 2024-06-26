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
from Bard import Chatbot
import logging
from os import path
from json import load
from json import dumps
import warnings
logging.getLogger("httpx").setLevel(logging.ERROR)
warnings.simplefilter("ignore", category=UserWarning)
class GEMINI(Provider):
    def __init__(
        self,
        cookie_file: str,
        proxy: dict = {},
        timeout: int = 30,
    ):
        """Initializes GEMINI

        Args:
            cookie_file (str): Path to `bard.google.com.cookies.json` file
            proxy (dict, optional): Http request proxy. Defaults to {}.
            timeout (int, optional): Http request timeout. Defaults to 30.
        """
        self.conversation = Conversation(False)
        self.session_auth1 = None
        self.session_auth2 = None
        assert isinstance(
            cookie_file, str
        ), f"cookie_file should be of {str} only not '{type(cookie_file)}'"
        if path.isfile(cookie_file):
            # let's assume auth is a path to exported .json cookie-file
            with open(cookie_file) as fh:
                entries = load(fh)
            for entry in entries:
                if entry["name"] == "__Secure-1PSID":
                    self.session_auth1 = entry["value"]
                elif entry["name"] == "__Secure-1PSIDTS":
                    self.session_auth2 = entry["value"]

            assert all(
                [self.session_auth1, self.session_auth2]
            ), f"Failed to extract the required cookie value from file '{cookie_file}'"
        else:
            raise Exception(f"{cookie_file} is not a valid file path")

        self.session = Chatbot(self.session_auth1, self.session_auth2, proxy, timeout)
        self.last_response = {}
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
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
                optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defeaults to None
                conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            Returns:
               dict : {}
            ```json
            {
                "content": "General Kenobi! \n\n(I couldn't help but respond with the iconic Star Wars greeting since you used it first. )\n\nIs there anything I can help you with today?\n[Image of Hello there General Kenobi]",
                "conversation_id": "c_f13f6217f9a997aa",
                "response_id": "r_d3665f95975c368f",
                "factualityQueries": null,
                "textQuery": [
                    "hello there",
                    1
                    ],
                "choices": [
                    {
                        "id": "rc_ea075c9671bfd8cb",
                        "content": [
                            "General Kenobi! \n\n(I couldn't help but respond with the iconic Star Wars greeting since you used it first. )\n\nIs there anything I can help you with today?\n[Image of Hello there General Kenobi]"
                        ]
                    },
                    {
                        "id": "rc_de6dd3fb793a5402",
                        "content": [
                            "General Kenobi! (or just a friendly hello, whichever you prefer!). \n\nI see you're a person of culture as well. *Star Wars* references are always appreciated.  \n\nHow can I help you today?\n"
                            ]
                    },
                {
                    "id": "rc_a672ac089caf32db",
                    "content": [
                        "General Kenobi! (or just a friendly hello if you're not a Star Wars fan!). \n\nHow can I help you today? Feel free to ask me anything, or tell me what you'd like to chat about. I'm here to assist in any way I can.\n[Image of Obi-Wan Kenobi saying hello there]"
                    ]
                }
            ],

            "images": [
                "https://i.pinimg.com/originals/40/74/60/407460925c9e419d82b93313f0b42f71.jpg"
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
            response = self.session.ask(prompt)
            self.last_response.update(response)
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            yield dumps(response) if raw else response

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
        return response["content"]

    def reset(self):
        """Reset the current conversation"""
        self.session.async_chatbot.conversation_id = ""
        self.session.async_chatbot.response_id = ""
        self.session.async_chatbot.choice_id = ""