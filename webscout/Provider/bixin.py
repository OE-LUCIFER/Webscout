import requests
import json
import random
from typing import Any, Dict, Optional, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions


class Bixin(Provider):
    """
    A class to interact with the Bixin API.
    """

    AVAILABLE_MODELS = [
        'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-16k-0613', 'gpt-4-turbo', 'qwen-turbo'
    ]

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
        model: str = 'gpt-4-turbo',  # Default model
        system_prompt: str = "You are a helpful assistant.",
    ):
        """
        Initializes the Bixin API with given parameters.

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): AI model to use. Defaults to "gpt-4-turbo".
            system_prompt (str, optional): System prompt for Bixin.
                                   Defaults to "You are a helpful assistant.".
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://chat.bixin123.com/api/chatgpt/chat-process"
        self.stream_chunk_size = 1024
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Fingerprint": self.generate_fingerprint(),
            "Origin": "https://chat.bixin123.com",
            "Pragma": "no-cache",
            "Priority": "u=1, i",
            "Referer": "https://chat.bixin123.com/chat",
            "Sec-CH-UA": '"Chromium";v="127", "Not)A;Brand";v="99"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Linux"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "X-Website-Domain": "chat.bixin123.com",
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

    def generate_fingerprint(self) -> str:
        """
        Generates a random fingerprint number as a string.
        """
        return str(random.randint(100000000, 999999999))

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with Bixin

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
           "text" : "How may I assist you today?"
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

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": conversation_prompt},
        ]

        data = {
            "prompt": self.format_prompt(messages),
            "options": {
                "usingNetwork": False,
                "file": ""
            }
        }

        def for_stream():
            try:
                with requests.post(self.api_endpoint, headers=self.headers, json=data, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()

                    # Initialize variable to keep track of the last printed text
                    previous_text = ""

                    full_response = ''
                    for chunk in response.iter_content(chunk_size=self.stream_chunk_size, decode_unicode=True):
                        if chunk:
                            try:
                                json_chunk = json.loads(chunk)
                                text = json_chunk.get("text", "")

                                # Determine the new text to print
                                if text.startswith(previous_text):
                                    new_text = text[len(previous_text):]
                                    full_response += new_text
                                    yield new_text if raw else dict(text=full_response)
                                    previous_text = text
                                else:
                                    full_response += text
                                    yield text if raw else dict(text=full_response)
                                    previous_text = text
                            except json.JSONDecodeError:
                                # If the chunk isn't a complete JSON object, skip it
                                continue
                    self.last_response.update(dict(text=full_response))
                    self.conversation.update_chat_history(
                        prompt, self.get_message(self.last_response)
                    )
            except requests.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"\nRequest failed: {e}")

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def format_prompt(self, messages: list) -> str:
        """
        Formats the list of messages into a single prompt string.
        """
        formatted_messages = []
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            formatted_messages.append(f"{role}: {content}")
        return "\n".join(formatted_messages)

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

if __name__ == "__main__":
    from rich import print

    ai = Bixin()
    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)