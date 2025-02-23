
#!/usr/bin/env python3
"""
A merged API client for Free2GPT that supports both GPT and Claude variants
in a non-streaming manner. The client sends requests to the appropriate endpoint
based on the chosen variant and returns the complete response as text.

Usage:
    python Free2GPT.py

Select the variant by passing the 'variant' parameter in the constructor:
    variant="claude"  --> Uses https://claude3.free2gpt.xyz/api/generate
    variant="gpt"     --> Uses https://chat1.free2gpt.com/api/generate
"""

from typing import Optional, Dict
import time
import json
import requests
from hashlib import sha256

from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.Litlogger import Logger, LogFormat
from webscout import LitAgent


class Free2GPT(Provider):
    """
    A class to interact with the Free2GPT API in a non-streaming way.
    Supports both GPT and Claude variants via the 'variant' parameter.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        system_prompt: str = "You are a helpful AI assistant.",
        variant: str = "claude"  # "claude" or "gpt"
    ):
        """
        Initializes the Free2GPT API client.

        Args:
            is_conversation (bool): Enable conversational mode. Defaults to True.
            max_tokens (int): Maximum tokens to generate. Defaults to 600.
            timeout (int): HTTP request timeout. Defaults to 30.
            intro (str, optional): Introductory prompt for the conversation. Defaults to None.
            filepath (str, optional): Path to conversation history file. Defaults to None.
            update_file (bool): Whether to update the conversation file. Defaults to True.
            proxies (dict): HTTP proxy settings. Defaults to empty dict.
            history_offset (int): Limit for conversation history. Defaults to 10250.
            act (str, optional): Awesome prompt key/index. Defaults to None.
            system_prompt (str): System prompt. Defaults to "You are a helpful AI assistant.".
            variant (str): Select API variant: "claude" or "gpt". Defaults to "claude".
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens

        # Select API endpoint and header origins based on variant.
        if variant.lower() == "gpt":
            self.api_endpoint = "https://chat1.free2gpt.com/api/generate"
            origin = "https://chat1.free2gpt.co"
        else:
            self.api_endpoint = "https://claude3.free2gpt.xyz/api/generate"
            origin = "https://claude3.free2gpt.xyz"

        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "text/plain;charset=UTF-8",
            "dnt": "1",
            "origin": origin,
            "referer": origin,
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": LitAgent().random(),
        }
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

        # Prepare available optimizers from Optimizers module.
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
        self.conversation = Conversation(is_conversation, self.max_tokens_to_sample, filepath, update_file)
        self.conversation.history_offset = history_offset

    def generate_signature(self, time_val: int, text: str, secret: str = "") -> str:
        """
        Generates a signature for the request.

        Args:
            time_val (int): Timestamp value.
            text (str): Text to sign.
            secret (str, optional): Optional secret. Defaults to "".

        Returns:
            str: Hexadecimal signature.
        """
        message = f"{time_val}:{text}:{secret}"
        return sha256(message.encode()).hexdigest()

    def ask(
        self,
        prompt: str,
        stream: bool = False,  # Ignored; always non-streaming.
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Dict[str, any]:
        """
        Sends a prompt to the API in a non-streaming manner.

        Args:
            prompt (str): The prompt text.
            stream (bool): Ignored; response is always non-streamed.
            raw (bool): Whether to return the raw response. Defaults to False.
            optimizer (str, optional): Optimizer name. Defaults to None.
            conversationally (bool): Whether to use conversational optimization. Defaults to False.

        Returns:
            dict: A dictionary containing the generated text.
                  Example:
                  {
                      "text": "How may I assist you today?"
                  }
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {list(self.__available_optimizers)}")

        # Generate timestamp and signature.
        timestamp = int(time.time() * 1e3)
        signature = self.generate_signature(timestamp, conversation_prompt)

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "time": timestamp,
            "pass": None,
            "sign": signature,
        }

        try:
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            response.raise_for_status()
            full_response = response.text
            self.last_response.update(dict(text=full_response))
            self.conversation.update_chat_history(prompt, self.get_message(self.last_response))
            return self.last_response
        except requests.exceptions.RequestException as e:
            raise exceptions.FailedToGenerateResponseError(f"An error occurred: {e}")

    def chat(
        self,
        prompt: str,
        stream: bool = False,  # Ignored; always non-streaming.
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> str:
        """
        Sends a prompt and returns the generated response as a string.

        Args:
            prompt (str): The prompt to send.
            stream (bool): Ignored; response is always non-streamed.
            optimizer (str, optional): Optimizer name. Defaults to None.
            conversationally (bool): Whether to use conversational optimization. Defaults to False.

        Returns:
            str: Generated response.
        """
        response = self.ask(
            prompt,
            stream=False,
            optimizer=optimizer,
            conversationally=conversationally,
        )
        return self.get_message(response)

    def get_message(self, response: Dict[str, any]) -> str:
        """
        Extracts the message text from the API response.

        Args:
            response (dict): The API response.

        Returns:
            str: Extracted message text.
        """
        assert isinstance(response, dict), "Response should be a dictionary"
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')


if __name__ == "__main__":
    from rich import print
    prompt_input = input(">>> ")
    # Choose variant: "claude" or "gpt"
    client = Free2GPT(variant="gpt")
    result = client.chat(prompt_input)
    print(result)
