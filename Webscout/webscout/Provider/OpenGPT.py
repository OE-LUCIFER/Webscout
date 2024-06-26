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

class OPENGPTv2(Provider):
    def __init__(
        self,
        generate_new_agents: bool = False,
        assistant_name: str = "webscout",
        retrieval_description: str = (
            "Can be used to look up information that was uploaded to this assistant.\n"
            "If the user is referencing particular files, that is often a good hint that information may be here.\n"
            "If the user asks a vague question, they are likely meaning to look up info from this retriever, "
            "and you should call it!"
        ),
        agent_system_message: str = "You are a helpful assistant.",
        chat_retrieval_llm_type: str = "GPT 3.5 Turbo",
        chat_retrieval_system_message: str = "You are a helpful assistant.",
        chatbot_llm_type: str = "GPT 3.5 Turbo",
        chatbot_system_message: str = "You are a helpful assistant.",
        enable_action_server: bool = False,
        enable_ddg_search: bool = False,
        enable_arxiv: bool = False,
        enable_press_releases: bool = False,
        enable_pubmed: bool = False,
        enable_sec_filings: bool = False,
        enable_retrieval: bool = False,
        enable_search_tavily: bool = False,
        enable_search_short_answer_tavily: bool = False,
        enable_you_com_search: bool = False,
        enable_wikipedia: bool = False,
        is_public: bool = True,
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
        """
        Initializes the OPENGPTv2 Provider.

        Args:
            api_endpoint: The API endpoint for OpenGPTs.
            generate_new_agents: If True, generates new assistant and user IDs.
            assistant_name: The name of the assistant to create if generating new IDs.
            agent_type: The type of agent to create.
            retrieval_description: Description of the retrieval tool.
            agent_system_message: System message for the agent.
            chat_retrieval_llm_type: LLM type for chat retrieval.
            chat_retrieval_system_message: System message for chat retrieval.
            chatbot_llm_type: LLM type for the chatbot.
            chatbot_system_message: System message for the chatbot.
            enable_action_server: Whether to enable the "Action Server by Robocorp" tool.
            enable_ddg_search: Whether to enable the "Duck Duck Go Search" tool.
            enable_arxiv: Whether to enable the "Arxiv" tool.
            enable_press_releases: Whether to enable the "Press Releases (Kay.ai)" tool.
            enable_pubmed: Whether to enable the "PubMed" tool.
            enable_sec_filings: Whether to enable the "SEC Filings (Kay.ai)" tool.
            enable_retrieval: Whether to enable the "Retrieval" tool.
            enable_search_tavily: Whether to enable the "Search (Tavily)" tool.
            enable_search_short_answer_tavily: Whether to enable the "Search (short answer, Tavily)" tool.
            enable_you_com_search: Whether to enable the "You.com Search" tool.
            enable_wikipedia: Whether to enable the "Wikipedia" tool.
            is_public: Whether the assistant should be public.
            is_conversation: Whether to maintain conversation history.
            max_tokens: Maximum tokens for responses.
            timeout: Timeout for API requests.
            intro: Initial prompt.
            filepath: Path to store conversation history.
            update_file: Whether to update the conversation history file.
            proxies: Proxies to use for requests.
            history_offset: Maximum conversation history size.
            act: Key for Awesome Prompts to use as intro.
        """
        self.api_endpoint = "https://opengpts-example-vz4y4ooboq-uc.a.run.app/runs/stream"
        self.session = requests.Session()
        self.ids_file = "openGPT_IDs.txt"
        agent_type="GPT 3.5 Turbo"
        (
            self.assistant_id,
            self.user_id,
        ) = self._manage_assistant_and_user_ids(
            generate_new_agents,
            assistant_name,
            agent_type,
            retrieval_description,
            agent_system_message,
            chat_retrieval_llm_type,
            chat_retrieval_system_message,
            chatbot_llm_type,
            chatbot_system_message,
            enable_action_server,
            enable_ddg_search,
            enable_arxiv,
            enable_press_releases,
            enable_pubmed,
            enable_sec_filings,
            enable_retrieval,
            enable_search_tavily,
            enable_search_short_answer_tavily,
            enable_you_com_search,
            enable_wikipedia,
            is_public,
        )
        self.last_response = {}
        self.max_tokens_to_sample = max_tokens
        self.stream_chunk_size = 64
        self.timeout = timeout
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
            is_conversation,
            self.max_tokens_to_sample,
            filepath,
            update_file,
        )
        self.conversation.history_offset = history_offset
        self.session.proxies.update(proxies)

    def _manage_assistant_and_user_ids(
        self,
        generate_new_agents: bool = False,
        assistant_name: str = "New Assistant",
        agent_type: str = "GPT 3.5 Turbo",
        retrieval_description: str = (
            "Can be used to look up information that was uploaded to this assistant.\n"
            "If the user is referencing particular files, that is often a good hint that information may be here.\n"
            "If the user asks a vague question, they are likely meaning to look up info from this retriever, "
            "and you should call it!"
        ),
        agent_system_message: str = "You are a helpful assistant.",
        chat_retrieval_llm_type: str = "GPT 3.5 Turbo",
        chat_retrieval_system_message: str = "You are a helpful assistant.",
        chatbot_llm_type: str = "GPT 3.5 Turbo",
        chatbot_system_message: str = "You are a helpful assistant.",
        enable_action_server: bool = False,
        enable_ddg_search: bool = False,
        enable_arxiv: bool = False,
        enable_press_releases: bool = False,
        enable_pubmed: bool = False,
        enable_sec_filings: bool = False,
        enable_retrieval: bool = False,
        enable_search_tavily: bool = False,
        enable_search_short_answer_tavily: bool = False,
        enable_you_com_search: bool = False,
        enable_wikipedia: bool = False,
        is_public: bool = True,
    ) -> tuple[str, str]:
        """
        Generates or retrieves assistant and user IDs.

        If 'generate_new_agents' is True, new IDs are created and saved to 'openGPT_IDs.txt'.
        Otherwise, IDs are loaded from 'openGPT_IDs.txt'.

        Args:
            generate_new_agents: If True, generate new IDs; otherwise, load from the file.
            assistant_name: The name of the assistant (used when generating new IDs).
            agent_type: The type of the agent.
            retrieval_description: Description for the retrieval tool.
            agent_system_message: The system message for the agent.
            chat_retrieval_llm_type: The LLM type for chat retrieval.
            chat_retrieval_system_message: The system message for chat retrieval.
            chatbot_llm_type: The LLM type for the chatbot.
            chatbot_system_message: The system message for the chatbot.
            enable_action_server: Whether to enable the "Action Server by Robocorp" tool.
            enable_ddg_search: Whether to enable the "Duck Duck Go Search" tool.
            enable_arxiv: Whether to enable the "Arxiv" tool.
            enable_press_releases: Whether to enable the "Press Releases (Kay.ai)" tool.
            enable_pubmed: Whether to enable the "PubMed" tool.
            enable_sec_filings: Whether to enable the "SEC Filings (Kay.ai)" tool.
            enable_retrieval: Whether to enable the "Retrieval" tool.
            enable_search_tavily: Whether to enable the "Search (Tavily)" tool.
            enable_search_short_answer_tavily: Whether to enable the "Search (short answer, Tavily)" tool.
            enable_you_com_search: Whether to enable the "You.com Search" tool.
            enable_wikipedia: Whether to enable the "Wikipedia" tool.
            is_public: Whether the assistant should be public.

        Returns:
            A tuple containing the assistant ID and user ID.
        """

        if generate_new_agents:
            user_id = str(uuid.uuid4())
            assistant_url = f"https://opengpts-example-vz4y4ooboq-uc.a.run.app/assistants/{str(uuid.uuid4())}"

            headers = {"Cookie": f"opengpts_user_id={user_id}"}

            tools = []
            if enable_action_server:
                tools.append("Action Server by Robocorp")
            if enable_ddg_search:
                tools.append("DDG Search")
            if enable_arxiv:
                tools.append("Arxiv")
            if enable_press_releases:
                tools.append("Press Releases (Kay.ai)")
            if enable_pubmed:
                tools.append("PubMed")
            if enable_sec_filings:
                tools.append("SEC Filings (Kay.ai)")
            if enable_retrieval:
                tools.append("Retrieval")
            if enable_search_tavily:
                tools.append("Search (Tavily)")
            if enable_search_short_answer_tavily:
                tools.append("Search (short answer, Tavily)")
            if enable_you_com_search:
                tools.append("You.com Search")
            if enable_wikipedia:
                tools.append("Wikipedia")

            payload = {
                "name": assistant_name,
                "config": {
                    "configurable": {
                        "thread_id": "",
                        "type": "agent",
                        "type==agent/agent_type": agent_type,
                        "type==agent/retrieval_description": retrieval_description,
                        "type==agent/system_message": agent_system_message,
                        "type==agent/tools": tools,
                        "type==chat_retrieval/llm_type": chat_retrieval_llm_type,
                        "type==chat_retrieval/system_message": chat_retrieval_system_message,
                        "type==chatbot/llm_type": chatbot_llm_type,
                        "type==chatbot/system_message": chatbot_system_message,
                    },
                    "public": is_public,
                },
            }

            response = requests.put(assistant_url, headers=headers, json=payload)
            response.raise_for_status()

            json_data = response.json()
            assistant_id = json_data["assistant_id"]

            with open(self.ids_file, "w") as f:  # Overwrite the file with new IDs
                f.write(f"Assistant ID: {assistant_id}\nUser ID: {user_id}\n")

            return assistant_id, user_id
        else:
            try:
                with open(self.ids_file, "r") as f:
                    lines = f.readlines()
                assistant_id = lines[0].split(":")[1].strip()
                user_id = lines[1].split(":")[1].strip()
                return assistant_id, user_id
            except FileNotFoundError:
                return None, None

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
        headers = {"Cookie": f"opengpts_user_id={self.user_id}"}
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

        response = self.session.post(
            self.api_endpoint, headers=headers, json=payload, stream=stream, timeout=self.timeout
        )
        complete_response = ""
        printed_length = 0
        initial_responses_to_ignore = 2

        for line in response.iter_lines(decode_unicode=True, chunk_size=1):
            if line:
                try:
                    content = json.loads(re.sub("data:", "", line))[-1]["content"]
                    if initial_responses_to_ignore > 0:
                        initial_responses_to_ignore -= 1
                    else:
                        if stream:
                            print(content[printed_length:], end="", flush=True)
                        printed_length = len(content)
                        complete_response = content
                except:
                    continue
        self.conversation.update_chat_history(prompt, complete_response)
        self.last_response.update(dict(text=complete_response))
        return self.last_response

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