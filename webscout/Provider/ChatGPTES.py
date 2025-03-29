import requests
import re
import json
import os
from typing import Union, List, Dict
from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from rich import print

class ChatGPTES(Provider):
    """
    A class to interact with the ChatGPT.es API.
    """

    SUPPORTED_MODELS = {
        'gpt-4o', 'gpt-4o-mini', 'chatgpt-4o-latest'
    }

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
        model: str = "chatgpt-4o-latest",  # Default model
        system_prompt: str = "You are a helpful assistant.",
    ):
        """
        Initializes the ChatGPT.es API with given parameters.
        """
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}. Choose from: {self.SUPPORTED_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = 'https://chatgpt.es/wp-admin/admin-ajax.php'
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.model = model
        self.initial_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/avif,image/webp,image/apng,*/*;q=0.8,'
                      'application/signed-exchange;v=b3;q=0.7',
        }
        self.post_headers = {
            'User-Agent': self.initial_headers['User-Agent'],
            'Referer': 'https://chatgpt.es/',
            'Origin': 'https://chatgpt.es',
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        self.nonce = None
        self.post_id = None

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        # Conversation setup
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

    def get_nonce_and_post_id(self):
        """
        Retrieves the nonce and post ID from the ChatGPT.es website.
        """
        try:
            response = self.session.get('https://chatgpt.es/', headers=self.initial_headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to retrieve nonce and post_id: {e}")

        nonce_match = re.search(r'data-nonce="(.+?)"', response.text)
        post_id_match = re.search(r'data-post-id="(.+?)"', response.text)

        if not nonce_match or not post_id_match:
            raise ValueError("Failed to parse nonce or post_id from the response.")

        self.nonce = nonce_match.group(1)
        self.post_id = post_id_match.group(1)

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """
        Chat with ChatGPT.es

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.

        Returns:
            dict: Response dictionary.
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                optimizer_func = getattr(Optimizers, optimizer)
                conversation_prompt = optimizer_func(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise ValueError(f"Optimizer '{optimizer}' is not supported. "
                                 f"Available optimizers: {list(self.__available_optimizers)}")

        # Retrieve nonce and post_id if they are not set
        if not self.nonce or not self.post_id:
            self.get_nonce_and_post_id()

        messages = [
            {"role": "user", "content": conversation_prompt},
        ]

        # Prepare conversation history
        conversation = ["Human: strictly respond in the same language as my prompt, preferably English"]
        for msg in messages:
            role = "Human" if msg['role'] == "user" else "AI"
            conversation.append(f"{role}: {msg['content']}")

        payload = {
            '_wpnonce': self.nonce,
            'post_id': self.post_id,
            'url': 'https://chatgpt.es',
            'action': 'wpaicg_chat_shortcode_message',
            'message': messages[-1]['content'],
            'bot_id': '0',
            'chatbot_identity': 'shortcode',
            'wpaicg_chat_client_id': os.urandom(5).hex(),
            'wpaicg_chat_history': json.dumps(conversation)
        }

        try:
            response = self.session.post(
                self.api_endpoint,
                headers=self.post_headers,
                data=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to send request to ChatGPT.es: {e}")

        try:
            response_data = response.json()
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response: {response.text}")

        if not isinstance(response_data, dict):
            raise TypeError(f"Expected response_data to be a dict, got {type(response_data)}")

        # Extract the message directly from the 'data' key
        message = response_data.get('data')
        if not isinstance(message, str):
            raise KeyError("Missing 'data' key in response or 'data' is not a string")

        self.last_response.update(dict(text=message))
        self.conversation.update_chat_history(
            prompt, self.get_message(self.last_response)
        )
        return self.last_response

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """
        Generate response as a string.

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.

        Returns:
            str: Response generated.
        """
        response = self.ask(
            prompt,
            stream=stream,
            optimizer=optimizer,
            conversationally=conversationally,
        )
        return self.get_message(response)

    def get_message(self, response: dict) -> str:
        """
        Retrieves message only from response.

        Args:
            response (dict): Response generated by `self.ask`.

        Returns:
            str: Message extracted.
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    ai = ChatGPTES() 
    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)

