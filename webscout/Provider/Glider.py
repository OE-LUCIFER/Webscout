import requests
import json
from typing import Any, Dict, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent as Lit


class GliderAI(Provider):
    """
    A class to interact with the Glider.so API.
    """

    AVAILABLE_MODELS = [
        "chat-llama-3-1-70b",
        "chat-llama-3-1-8b",
        "chat-llama-3-2-3b",
        "deepseek-ai/DeepSeek-R1",
    ]

    model_aliases = {
        "llama-3.1-70b": "chat-llama-3-1-70b",
        "llama-3.1-8b": "chat-llama-3-1-8b",
        "llama-3.2-3b": "chat-llama-3-2-3b",
        "deepseek-r1": "deepseek-ai/DeepSeek-R1",
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
        model: str = "llama-3.1-70b",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """Initializes the GliderAI API client."""
        if model not in self.AVAILABLE_MODELS and model not in self.model_aliases:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {', '.join(self.AVAILABLE_MODELS)}"
            )
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://glider.so/api/chat"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = self.model_aliases.get(model, model)
        self.system_prompt = system_prompt
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://glider.so",
            "referer": "https://glider.so/",
            "user-agent": Lit().random(),
        }
        self.session.headers.update(self.headers)
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
    ) -> Dict[str, Any] | Generator:
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

        payload = {
            "messages": [
                {"role": "user", "content": conversation_prompt},
                {"role": "system", "content": self.system_prompt},
            ],
            "model": self.model,
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_text = ""
            for value in response.iter_lines(decode_unicode=True):
                if value:
                    if value.startswith("data: "):
                        try:
                            data = json.loads(value[6:])
                            content = (
                                data["choices"][0].get("delta", {}).get("content", "")
                            )
                            if content:
                                streaming_text += content
                                yield content if raw else dict(text=content)
                        except json.JSONDecodeError:
                            if "stop" in value:
                                break

            self.last_response.update(dict(text=streaming_text))
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
    ) -> str | Generator[str, None, None]:
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
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]


if __name__ == "__main__":
    from rich import print

    ai = GliderAI(model="llama-3.1-70b")
    response = ai.chat("Meaning of Life", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
