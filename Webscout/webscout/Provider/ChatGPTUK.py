import requests
from typing import Any, AsyncGenerator, Dict, Optional
import json
import re

from ..AIutel import Optimizers
from ..AIutel import Conversation
from ..AIutel import AwesomePrompts, sanitize_stream
from ..AIbase import  Provider, AsyncProvider
from webscout import exceptions


class ChatGPTUK(Provider):
    """
    A class to interact with the ChatGPT UK API.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 0.9,
        presence_penalty: float = 0,
        frequency_penalty: float = 0,
        top_p: float = 1,
        model: str = "google-gemini-pro",
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ) -> None:
        """
        Initializes the ChatGPTUK API with given parameters.

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 0.9.
            presence_penalty (float, optional): Chances of topic being repeated. Defaults to 0.
            frequency_penalty (float, optional): Chances of word being repeated. Defaults to 0.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 1.
            model (str, optional): LLM model name. Defaults to "google-gemini-pro".
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://free.chatgpt.org.uk/api/openai/v1/chat/completions"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p
        self.headers = {"Content-Type": "application/json"}

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

        self.session.headers.update(self.headers)
        payload = {
            "messages": [
                {"role": "system", "content": "Keep your responses long and detailed"},
                {"role": "user", "content": conversation_prompt}
            ],
            "stream": True,
            "model": self.model,
            "temperature": self.temperature,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens_to_sample
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_response = ""
            for line in response.iter_lines(decode_unicode=True, chunk_size=1):
                if line:
                    modified_line = re.sub("data:", "", line)
                    try:
                        json_data = json.loads(modified_line)
                        content = json_data['choices'][0]['delta']['content']
                        streaming_response += content
                        yield content if raw else dict(text=streaming_response)
                    except:
                        continue
            self.last_response.update(dict(text=streaming_response))
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