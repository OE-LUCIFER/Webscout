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
#------------------------------------------------------PERPLEXITY--------------------------------------------------------  
class PERPLEXITY(Provider):
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
        quiet: bool = False,
    ):
        """Instantiates PERPLEXITY

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
            quiet (bool, optional): Ignore web search-results and yield final response only. Defaults to False.
        """
        self.max_tokens_to_sample = max_tokens
        self.is_conversation = is_conversation
        self.last_response = {}
        self.web_results: dict = {}
        self.quiet = quiet

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
            "status": "pending",
            "uuid": "3604dfcc-611f-4b7d-989d-edca2a7233c7",
            "read_write_token": null,
            "frontend_context_uuid": "f6d43119-5231-481d-b692-f52e1f52d2c6",
            "final": false,
            "backend_uuid": "a6d6ec9e-da69-4841-af74-0de0409267a8",
            "media_items": [],
            "widget_data": [],
            "knowledge_cards": [],
            "expect_search_results": "false",
            "mode": "concise",
            "search_focus": "internet",
            "gpt4": false,
            "display_model": "turbo",
            "attachments": null,
            "answer": "",
            "web_results": [],
            "chunks": [],
            "extra_web_results": []
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
            for response in Perplexity().generate_answer(conversation_prompt):
                yield json.dumps(response) if raw else response
                self.last_response.update(response)

            self.conversation.update_chat_history(
                prompt,
                self.get_message(self.last_response),
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
        text_str: str = response.get("answer", "")

        def update_web_results(web_results: list) -> None:
            for index, results in enumerate(web_results, start=1):
                self.web_results[str(index) + ". " + results["name"]] = dict(
                    url=results.get("url"), snippet=results.get("snippet")
                )

        if response.get("text"):
            # last chunk
            target: dict[str, Any] = json.loads(response.get("text"))
            text_str = target.get("answer")
            web_results: list[dict] = target.get("web_results")
            self.web_results.clear()
            update_web_results(web_results)

            return (
                text_str
                if self.quiet or not self.web_results
                else text_str + "\n\n# WEB-RESULTS\n\n" + yaml.dump(self.web_results)
            )

        else:
            if str(response.get("expect_search_results")).lower() == "true":
                return (
                    text_str
                    if self.quiet
                    else text_str
                    + "\n\n# WEB-RESULTS\n\n"
                    + yaml.dump(response.get("web_results"))
                )
            else:
                return text_str