import re
import requests
import json
import os
from typing import Any, Dict, Optional, Generator, List, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from fake_useragent import UserAgent
from cerebras.cloud.sdk import Cerebras


class Cerebras(Provider):
    """
    A class to interact with the Cerebras API using a cookie for authentication.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        cookie_path: str = "cookie.json",  # Path to cookie file
        model: str = "llama3.1-8b",  # Default model
        system_prompt: str = "You are a helpful assistant.",
    ):
        """
        Initializes the Cerebras client with the provided cookie.

        Args:
            cookie_path (str): Path to the cookie JSON file.
            model (str, optional): Model name to use. Defaults to 'llama3.1-8b'.
            system_prompt (str, optional): The system prompt to send with every request. Defaults to "You are a helpful assistant.".

        Raises:
            FileNotFoundError: If the cookie file is not found.
            json.JSONDecodeError: If the cookie file has an invalid JSON format.
            requests.exceptions.RequestException: If there's an error retrieving the API key.
        """
        self.api_key = self.get_demo_api_key(cookie_path)
        self.client = Cerebras(api_key=self.api_key)
        self.model = model
        self.system_prompt = system_prompt

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
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


    @staticmethod
    def extract_query(text: str) -> str:
        """
        Extracts the first code block from the given text.
        """
        pattern = r"```(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches[0].strip() if matches else text.strip()

    @staticmethod
    def refiner(text: str) -> str:
        """Refines the input text by removing surrounding quotes."""
        return text.strip('"')

    def get_demo_api_key(self, cookie_path: str) -> str:
        """Retrieves the demo API key using the provided cookie."""
        try:
            with open(cookie_path, "r") as file:
                cookies = {item["name"]: item["value"] for item in json.load(file)}
        except FileNotFoundError:
            raise FileNotFoundError(f"Cookie file not found at path: {cookie_path}")
        except json.JSONDecodeError:
            raise json.JSONDecodeError("Invalid JSON format in the cookie file.")

        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://inference.cerebras.ai",
            "Referer": "https://inference.cerebras.ai/",
            "user-agent": UserAgent().random,
        }

        json_data = {
            "operationName": "GetMyDemoApiKey",
            "variables": {},
            "query": "query GetMyDemoApiKey {\n  GetMyDemoApiKey\n}",
        }

        try:
            response = requests.post(
                "https://inference.cerebras.ai/api/graphql",
                cookies=cookies,
                headers=headers,
                json=json_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            api_key = response.json()["data"]["GetMyDemoApiKey"]
            return api_key
        except requests.exceptions.RequestException as e:
            raise exceptions.APIConnectionError(f"Failed to retrieve API key: {e}")
        except KeyError:
            raise exceptions.InvalidResponseError("API key not found in response.")


    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict, Generator]:

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        messages = [
            {"content": self.system_prompt, "role": "system"},
            {"content": conversation_prompt, "role": "user"},
        ]

        def for_stream():
            try:
                response = self.client.chat.completions.create(
                    model=self.model, messages=messages, stream=True
                )
                for choice in response.choices:
                    if choice.delta.content:
                        yield dict(text=choice.delta.content)
                self.last_response.update({"text": response.choices[0].message.content})

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Error during stream: {e}")

        def for_non_stream():
            try:
                response = self.client.chat.completions.create(
                    model=self.model, messages=messages
                )
                self.last_response.update({"text": response.choices[0].message.content})
                return self.last_response
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Error during non-stream: {e}")

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator]:
        return self.get_message(
            self.ask(
                prompt, stream, optimizer=optimizer, conversationally=conversationally
            )
        )

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]


if __name__ == "__main__":
    from rich import print
    cerebras = Cerebras(cookie_path='cookie.json', model='llama3.1-8b', system_prompt="You are a helpful AI assistant.")
    response = cerebras.chat("What is the meaning of life?", sys_prompt='', stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)