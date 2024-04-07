import time
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
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from Helpingai_T2 import Perplexity
from typing import Any
import logging
#------------------------------------------------------KOBOLDAI-----------------------------------------------------------
class KOBOLDAI(Provider):
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 1,
        top_p: float = 1,
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
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 0.2.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 0.999.
            timeout (int, optional): Http requesting timeout. Defaults to 30
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
        self.temperature = temperature
        self.top_p = top_p
        self.chat_endpoint = (
            "https://koboldai-koboldcpp-tiefighter.hf.space/api/extra/generate/stream"
        )
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
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
           "token" : "How may I assist you today?"
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
            "prompt": conversation_prompt,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            message_load = ""
            for value in response.iter_lines(
                decode_unicode=True,
                delimiter="" if raw else "event: message\ndata:",
                chunk_size=self.stream_chunk_size,
            ):
                try:
                    resp = json.loads(value)
                    message_load += self.get_message(resp)
                    resp["token"] = message_load
                    self.last_response.update(resp)
                    yield value if raw else resp
                except json.decoder.JSONDecodeError:
                    pass
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

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
        return response.get("token")
#------------------------------------------------------OpenGPT-----------------------------------------------------------
class OPENGPT:
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
        self.session = requests.Session()
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
#------------------------------------------------------PERPLEXITY--------------------------------------------------------  
class PERPLEXITY:
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 8000,
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
        logging.getLogger("websocket").setLevel(logging.ERROR)
        self.session = requests.Session()
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
#------------------------------------------------------BLACKBOXAI--------------------------------------------------------  
class BLACKBOXAI:
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 8000,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = None,
    ):
        """Instantiates BLACKBOXAI

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
            model (str, optional): Model name. Defaults to "Phind Model".
        """
        self.session = requests.Session()
        self.max_tokens_to_sample = max_tokens
        self.is_conversation = is_conversation
        self.chat_endpoint = "https://www.blackbox.ai/api/chat"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.previewToken: str = None
        self.userId: str = ""
        self.codeModelMode: bool = True
        self.id: str = ""
        self.agentMode: dict = {}
        self.trendingAgentMode: dict = {}
        self.isMicMode: bool = False

        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "",
            "Accept": "*/*",
            "Accept-Encoding": "Identity",
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
           "text" : "print('How may I help you today?')"
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
            "messages": [
                # json.loads(prev_messages),
                {"content": conversation_prompt, "role": "user"}
            ],
            "id": self.id,
            "previewToken": self.previewToken,
            "userId": self.userId,
            "codeModelMode": self.codeModelMode,
            "agentMode": self.agentMode,
            "trendingAgentMode": self.trendingAgentMode,
            "isMicMode": self.isMicMode,
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if (
                not response.ok
                or not response.headers.get("Content-Type")
                == "text/plain; charset=utf-8"
            ):
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )
            streaming_text = ""
            for value in response.iter_lines(
                decode_unicode=True,
                chunk_size=self.stream_chunk_size,
                delimiter="\n",
            ):
                try:
                    if bool(value):
                        streaming_text += value + ("\n" if stream else "")

                        resp = dict(text=streaming_text)
                        self.last_response.update(resp)
                        yield value if raw else resp
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
        return response["text"]
    @staticmethod
    def chat_cli(prompt):
        """Sends a request to the BLACKBOXAI API and processes the response."""
        blackbox_ai = BLACKBOXAI()  # Initialize a BLACKBOXAI instance
        response = blackbox_ai.ask(prompt)  # Perform a chat with the given prompt
        processed_response = blackbox_ai.get_message(response)  # Process the response
        print(processed_response)
#------------------------------------------------------phind-------------------------------------------------------------
class PhindSearch:
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 8000,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "Phind Model",
        quiet: bool = False,
    ):
        """Instantiates PHIND

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
            model (str, optional): Model name. Defaults to "Phind Model".
            quiet (bool, optional): Ignore web search-results and yield final response only. Defaults to False.
        """
        self.session = requests.Session()
        self.max_tokens_to_sample = max_tokens
        self.is_conversation = is_conversation
        self.chat_endpoint = "https://https.extension.phind.com/agent/"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.quiet = quiet

        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "",
            "Accept": "*/*",
            "Accept-Encoding": "Identity",
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
            "id": "chatcmpl-r0wujizf2i2xb60mjiwt",
            "object": "chat.completion.chunk",
            "created": 1706775384,
            "model": "trt-llm-phind-model-serving",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": "Hello! How can I assist you with your programming today?"
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
            "additional_extension_context": "",
            "allow_magic_buttons": True,
            "is_vscode_extension": True,
            "message_history": [
                {"content": conversation_prompt, "metadata": {}, "role": "user"}
            ],
            "requested_model": self.model,
            "user_input": prompt,
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
            streaming_text = ""
            for value in response.iter_lines(
                decode_unicode=True,
                chunk_size=self.stream_chunk_size,
            ):
                try:
                    modified_value = re.sub("data:", "", value)
                    json_modified_value = json.loads(modified_value)
                    retrieved_text = self.get_message(json_modified_value)
                    if not retrieved_text:
                        continue
                    streaming_text += retrieved_text
                    json_modified_value["choices"][0]["delta"][
                        "content"
                    ] = streaming_text
                    self.last_response.update(json_modified_value)
                    yield value if raw else json_modified_value
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
        if response.get("type", "") == "metadata":
            return

        delta: dict = response["choices"][0]["delta"]

        if not delta:
            return ""

        elif delta.get("function_call"):
            if self.quiet:
                return ""

            function_call: dict = delta["function_call"]
            if function_call.get("name"):
                return function_call["name"]
            elif function_call.get("arguments"):
                return function_call.get("arguments")

        elif delta.get("metadata"):
            if self.quiet:
                return ""
            return yaml.dump(delta["metadata"])

        else:
            return (
                response["choices"][0]["delta"].get("content")
                if response["choices"][0].get("finish_reason") is None
                else ""
            )
    @staticmethod
    def chat_cli(prompt):
        """Sends a request to the Phind API and processes the response."""
        phind_search = PhindSearch()  # Initialize a PhindSearch instance
        response = phind_search.ask(prompt)  # Perform a search with the given prompt
        processed_response = phind_search.get_message(response)  # Process the response
        print(processed_response)
#-------------------------------------------------------yep.com--------------------------------------------------------   
class YepChat:
    def __init__(self, message="hello"):
        self.url = "https://api.yep.com/v1/chat/completions"
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Content-Type": "application/json; charset=utf-8",
            "Origin": "https://yep.com",
            "Referer": "https://yep.com/",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT   10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0.0.0 Safari/537.36"
        }
        self.payload = {
            "stream": True,
            "max_tokens":   1280,
            "top_p":   0.7,
            "temperature":   0.6,
            "messages": [{
                "content": message,
                "role": "user"
            }],
            "model": "Mixtral-8x7B-Instruct-v0.1"
        }

    def send_request(self):
        response = requests.post(self.url, headers=self.headers, data=json.dumps(self.payload), stream=True)
        print(response.status_code)
        return response

    def process_response(self, response):
        myset = ""
        for line in response.iter_lines():
            if line:
                myline = line.decode('utf-8').removeprefix("data: ").replace(" null", "False")
                try:
                    myval = eval(myline)
                    if "choices" in myval and "delta" in myval["choices"][0] and "content" in myval["choices"][0]["delta"]:
                        myset += myval["choices"][0]["delta"]["content"]
                except:
                    continue
        return myset

    @staticmethod
    def chat_cli(message):
        """Sends a request to the Yep API and processes the response."""
        yep_chat = YepChat(message=message)
        response = yep_chat.send_request()
        processed_response = yep_chat.process_response(response)
        print(processed_response)
#-------------------------------------------------------youchat--------------------------------------------------------   
class youChat:
    """
    This class provides methods for generating completions based on prompts.
    """
    def create(self, prompt):
        """
        Generate a completion based on the provided prompt.

        Args:
            prompt (str): The input prompt to generate a completion from.

        Returns:
            str: The generated completion as a text string.

        Raises:
            Exception: If the response does not contain the expected "youChatToken".
        """
        resp = get(
            "https://you.com/api/streamingSearch",
            headers={
                "cache-control": "no-cache",
                "referer": "https://you.com/search?q=gpt4&tbm=youchat",
                "cookie": f"safesearch_guest=Off; uuid_guest={str(uuid4())}",
            },
            params={
                "q": prompt,
                "page": 1,
                "count": 10,
                "safeSearch": "Off",
                "onShoppingPage": False,
                "mkt": "",
                "responseFilter": "WebPages,Translations,TimeZone,Computation,RelatedSearches",
                "domain": "youchat",
                "queryTraceId": str(uuid4()),
                "chat": [],
            },
            impersonate="chrome107",
        )
        if "youChatToken" not in resp.text:
            raise RequestsError("Unable to fetch the response.")
        return (
            "".join(
                findall(
                    r"{\"youChatToken\": \"(.*?)\"}",
                    resp.content.decode("unicode-escape"),
                )
            )
            .replace("\\n", "\n")
            .replace("\\\\", "\\")
            .replace('\\"', '"')
        )

    @staticmethod
    def chat_cli(prompt):
        """Generate completion based on the provided prompt"""
        you_chat = youChat()
        completion = you_chat.create(prompt)
        print(completion)
#-------------------------------------------------------Gemini--------------------------------------------------------        
class Gemini:
    def __init__(self):
        self.messages = []

    def chat(self, *args):
        assert args != ()

        message = " ".join(args)
        self.messages.append({"role": "user", "content": message})

        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            provider=g4f.Provider.Gemini,
            messages=self.messages,
            stream=True,
        )
        ms = ""
        for message in response:
            ms += message
        self.messages.append({"role": "assistant", "content": ms.strip()}) # Strip whitespace from the message content
        return ms.strip() # Return the message without trailing whitespace

    @staticmethod
    def chat_cli(message):
        """Generate completion based on the provided message"""
        gemini = Gemini()
        return gemini.chat(message)
#-------------------------------------------------------Prodia-------------------------------------------------------------------------
class Prodia:
    """
    This class provides methods for generating images based on prompts.
    """

    def create(self, prompt):
        """
        Create a new image generation based on the given prompt.

        Args:
            prompt (str): The prompt for generating the image.

        Returns:
            resp: The generated image content
        """
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
        }
        try:
            resp = get(
                "https://api.prodia.com/generate",
                params={
                    "new": "true",
                    "prompt": prompt,
                    "model": "dreamshaper_6BakedVae.safetensors [114c8abb]",
                    "negative_prompt": "(nsfw:1.5),verybadimagenegative_v1.3, ng_deepnegative_v1_75t, (ugly face:0.5),cross-eyed,sketches, (worst quality:2), (low quality:2.1), (normal quality:2), lowres, normal quality, ((monochrome)), ((grayscale)), skin spots, acnes, skin blemishes, bad anatomy, DeepNegative, facing away, tilted head, {Multiple people}, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worstquality, low quality, normal quality, jpegartifacts, signature, watermark, username, blurry, bad feet, cropped, poorly drawn hands, poorly drawn face, mutation, deformed, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, extra fingers, fewer digits, extra limbs, extra arms,extra legs, malformed limbs, fused fingers, too many fingers, long neck, cross-eyed,mutated hands, polar lowres, bad body, bad proportions, gross proportions, text, error, missing fingers, missing arms, missing legs, extra digit, extra arms, extra leg, extra foot, repeating hair",
                    "steps": "50",
                    "cfg": "9.5",
                    "seed": randint(1, 10000),
                    "sampler": "Euler",
                    "aspect_ratio": "square",
                },
                headers=headers,
                timeout=30,
            )
            data = resp.json()
            while True:
                resp = get(f"https://api.prodia.com/job/{data['job']}", headers=headers)
                json = resp.json()
                if json["status"] == "succeeded":
                    return get(
                        f"https://images.prodia.xyz/{data['job']}.png?download=1",
                        headers=headers,
                    ).content
        except RequestException as exc:
            raise RequestException("Unable to fetch the response.") from exc

    @staticmethod
    def prodia_cli(prompt):
        """Generate an image based on the provided prompt."""
        generator = Prodia()
        try:
            image_content = generator.create(prompt)
            # Save the image content to a file
            with open('generated_image.png', 'wb') as f:
                f.write(image_content)
            print("Image generated successfully and saved as generated_image.png")
            
            # Open the image file and display it
            image = Image.open('generated_image.png')
            image.show()
        except Exception as e:
            print(f"An error occurred: {e}")
#-------------------------------------------------------Pollination--------------------------------------------------------------------------------------
class Pollinations:
    """
    This class provides methods for generating images based on prompts.
    """

    def create(self, prompt):
        """
        Create a new image generation based on the given prompt.

        Args:
            prompt (str): The prompt for generating the image.

        Returns:
            resp: The generated image content
        """
        try:
            return get(
                url=f"https://image.pollinations.ai/prompt/{prompt}{randint(1, 10000)}",
                timeout=30,
            ).content
        except RequestException as exc:
            raise RequestException("Unable to fetch the response.") from exc

    @staticmethod
    def pollinations_cli(prompt):
        """Generate an image based on the provided prompt."""
        generator = Pollinations()
        try:
            image_content = generator.create(prompt)
            # Save the image content to a file
            with open('generated_image.png', 'wb') as f:
                f.write(image_content)
            print("Image generated successfully and saved as generated_image.png")
            
            # Open the image file and display it
            image = Image.open('generated_image.png')
            image.show()
        except Exception as e:
            print(f"An error occurred: {e}")

@click.group()
def cli():
    """Webscout AI command-line interface."""
    pass

@cli.command()
@click.option('--prompt', prompt='Enter your search prompt', help='The prompt to send.')
def phindsearch(prompt):
    """Perform a search with the given prompt using PhindSearch."""
    phind_search = PhindSearch() # Initialize a PhindSearch instance
    response = phind_search.ask(prompt) # Perform a search with the given prompt
    processed_response = phind_search.get_message(response) # Process the response
    print(processed_response)

@cli.command()
@click.option('--message', prompt='Enter your message', help='The message to send.')
def yepchat(message):
    YepChat.chat_cli(message)

@cli.command()
@click.option('--prompt', prompt='Enter your prompt', help='The prompt to generate a completion from.')
def youchat(prompt):
    youChat.chat_cli(prompt)

@cli.command()
@click.option('--message', prompt='Enter your message', help='The message to send.')
def gemini(message):
    Gemini.chat_cli(message)

@cli.command()
@click.option('--prompt', prompt='Enter your prompt', help='The prompt for generating the image.')
def prodia(prompt):
    """Generate an image based on the provided prompt."""
    Prodia.prodia_cli(prompt)

@cli.command()
@click.option('--prompt', prompt='Enter your prompt', help='The prompt for generating the image.')
def pollinations(prompt):
    """Generate an image based on the provided prompt."""
    Pollinations.pollinations_cli(prompt)
    
@cli.command()
@click.option('--prompt', prompt='Enter your prompt', help='The prompt to send.')
def blackboxai(prompt):
    """Chat with BLACKBOXAI using the provided prompt."""
    BLACKBOXAI.chat_cli(prompt)
    
@cli.command()
@click.option('--prompt', prompt='Enter your prompt', help='The prompt to send.')
@click.option('--stream', is_flag=True, help='Flag for streaming response.')
@click.option('--raw', is_flag=True, help='Stream back raw response as received.')
@click.option('--optimizer', type=str, help='Prompt optimizer name.')
@click.option('--conversationally', is_flag=True, help='Chat conversationally when using optimizer.')
def perplexity(prompt, stream, raw, optimizer, conversationally):
    """Chat with PERPLEXITY using the provided prompt."""
    perplexity_instance = PERPLEXITY() # Initialize a PERPLEXITY instance
    response = perplexity_instance.ask(prompt, stream, raw, optimizer, conversationally)
    processed_response = perplexity_instance.get_message(response) # Process the response
    print(processed_response)
   
@cli.command()
@click.option('--prompt', prompt='Enter your search prompt', help='The prompt to send.')
@click.option('--stream', is_flag=True, help='Flag for streaming response.')
def opengpt(prompt, stream):
    """Chat with OPENGPT using the provided prompt."""
    opengpt = OPENGPT(is_conversation=True, max_tokens=8000, timeout=30)
    if stream:
        for response in opengpt.chat(prompt, stream=True):
            print(response)
    else:
        response_str = opengpt.chat(prompt)
        print(response_str)
        
@cli.command()
@click.option('--prompt', prompt='Enter your prompt', help='The prompt to send.')
@click.option('--stream', is_flag=True, help='Flag for streaming response.')
@click.option('--raw', is_flag=True, help='Stream back raw response as received.')
@click.option('--optimizer', type=str, help='Prompt optimizer name.')
@click.option('--conversationally', is_flag=True, help='Chat conversationally when using optimizer.')
def koboldai_cli(prompt, stream, raw, optimizer, conversationally):
    """Chat with KOBOLDAI using the provided prompt."""
    koboldai_instance = KOBOLDAI() # Initialize a KOBOLDAI instance
    response = koboldai_instance.ask(prompt, stream, raw, optimizer, conversationally)
    processed_response = koboldai_instance.get_message(response) # Process the response
    print(processed_response)
    
if __name__ == '__main__':
    cli()