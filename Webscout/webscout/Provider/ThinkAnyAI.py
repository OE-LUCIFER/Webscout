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
#------------------------------------ThinkAnyAI------------
class ThinkAnyAI(Provider):
    def __init__(
        self,
        model: str = "claude-3-haiku",
        locale: str = "en",
        web_search: bool = False,
        chunk_size: int = 1,
        streaming: bool = True,
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
        """Initializes ThinkAnyAI

        Args:
            model (str): The AI model to be used for generating responses. Defaults to "claude-3-haiku".
            locale (str): The language locale. Defaults to "en" (English).
            web_search (bool): Whether to include web search results in the response. Defaults to False.
            chunk_size (int): The size of data chunks when streaming responses. Defaults to 1.
            streaming (bool): Whether to stream response data. Defaults to True.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.base_url = "https://thinkany.ai/api"
        self.model = model
        self.locale = locale
        self.web_search = web_search
        self.chunk_size = chunk_size
        self.streaming = streaming
        self.last_response = {}
        self.session = requests.Session()
        self.session.proxies = proxies

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
            is_conversation, max_tokens, filepath, update_file
        )
        self.conversation.history_offset = history_offset

    def ask(
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

        def initiate_conversation(query: str) -> str:
            """
            Initiates a new conversation with the ThinkAny AI API.

            Args:
                query (str): The initial query to start the conversation.

            Returns:
                str: The UUID (Unique Identifier) of the conversation.
            """
            url = f"{self.base_url}/new-conversation"
            payload = {
                "content": query,
                "locale": self.locale,
                "mode": "search" if self.web_search else "chat",
                "model": self.model,
                "source": "all",
            }
            response = self.session.post(url, json=payload)
            return response.json().get("data", {}).get("uuid", "DevsDoCode")

        def RAG_search(uuid: str) -> tuple[bool, list]:
            """
            Performs a web search using the Retrieve And Generate (RAG) model.

            Args:
                uuid (str): The UUID of the conversation.

            Returns:
                tuple: A tuple containing a boolean indicating the success of the search
                        and a list of search result links.
            """
            if not self.web_search:
                return True, []
            url = f"{self.base_url}/rag-search"
            payload = {"conv_uuid": uuid}
            response = self.session.post(url, json=payload)
            links = [source["link"] for source in response.json().get("data", [])]
            return response.json().get("message", "").strip(), links

        def for_stream():
            conversation_uuid = initiate_conversation(conversation_prompt)
            web_search_result, links = RAG_search(conversation_uuid)
            if not web_search_result:
                print("Failed to generate WEB response. Making normal Query...")

            url = f"{self.base_url}/chat"
            payload = {
                "role": "user",
                "content": prompt,
                "conv_uuid": conversation_uuid,
                "model": self.model,
            }
            response = self.session.post(url, json=payload, stream=True)
            complete_content = ""
            for content in response.iter_content(
                decode_unicode=True, chunk_size=self.chunk_size
            ):
                complete_content += content
                yield content if raw else dict(text=complete_content)
            self.last_response.update(dict(text=complete_content, links=links))
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

    def get_message(self, response: Dict[str, Any]) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]