import re
import requests
import json
import os
from typing import Any, Dict, Optional, Generator, List, Union
from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from fake_useragent import UserAgent

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
        cookie_path: str = "cookie.json",
        model: str = "llama3.1-8b",
        system_prompt: str = "You are a helpful assistant.",
    ):
        # Initialize basic settings first
        self.timeout = timeout
        self.model = model
        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.last_response = {}

        # Get API key first
        try:
            self.api_key = self.get_demo_api_key(cookie_path)
        except Exception as e:
            raise exceptions.APIConnectionError(f"Failed to initialize Cerebras client: {e}")

        # Initialize optimizers
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        # Initialize conversation settings
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else None
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

    @staticmethod
    def extract_query(text: str) -> str:
        """Extracts the first code block from the given text."""
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
            raise json.JSONDecodeError("Invalid JSON format in the cookie file.", "", 0)

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

    def _make_request(self, messages: List[Dict], stream: bool = False) -> Union[Dict, Generator]:
        """Make a request to the Cerebras API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": UserAgent().random
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }

        try:
            response = requests.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                stream=stream,
                timeout=self.timeout
            )
            response.raise_for_status()

            if stream:
                def generate_stream():
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data:'):
                                try:
                                    data = json.loads(line[6:])
                                    if data.get('choices') and data['choices'][0].get('delta', {}).get('content'):
                                        content = data['choices'][0]['delta']['content']
                                        yield content
                                except json.JSONDecodeError:
                                    continue

                return generate_stream()
            else:
                response_json = response.json()
                return response_json['choices'][0]['message']['content']

        except requests.exceptions.RequestException as e:
            raise exceptions.APIConnectionError(f"Request failed: {e}")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict, Generator]:
        """Send a prompt to the model and get a response."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": conversation_prompt}
        ]

        try:
            response = self._make_request(messages, stream)
            if stream:
                return response
            
            self.last_response = response
            return response

        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Error during request: {e}")

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator]:
        """Chat with the model."""
        response = self.ask(prompt, stream, optimizer, conversationally)
        if stream:
            return response
        return response

    def get_message(self, response: str) -> str:
        """Retrieves message from response."""
        return response


if __name__ == "__main__":
    from rich import print
    
    # Example usage
    cerebras = Cerebras(
        cookie_path=r'C:\Users\koula\OneDrive\Desktop\Webscout\cookie.json',
        model='llama3.1-8b',
        system_prompt="You are a helpful AI assistant."
    )
    
    # Test with streaming
    response = cerebras.chat("Hello!", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
