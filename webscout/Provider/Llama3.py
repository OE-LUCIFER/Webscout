import requests
import json
from typing import Union, Any, Dict, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions

class Sambanova(Provider):
    """
    A class to interact with the Sambanova API.
    """

    AVAILABLE_MODELS = [
        "Meta-Llama-3.1-8B-Instruct",
        "Meta-Llama-3.1-70B-Instruct",
        "Meta-Llama-3.1-405B-Instruct",
        "DeepSeek-R1-Distill-Llama-70B",
        "Llama-3.1-Tulu-3-405B",
        "Meta-Llama-3.2-1B-Instruct",
        "Meta-Llama-3.2-3B-Instruct",
        "Meta-Llama-3.3-70B-Instruct",
        "Qwen2.5-72B-Instruct",
        "Qwen2.5-Coder-32B-Instruct",
        "QwQ-32B-Preview"
    ]

    def __init__(
        self,
        api_key: str = None,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "Meta-Llama-3.1-8B-Instruct",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """
        Initializes the Sambanova API with given parameters.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt

        self.session = requests.Session()
        self.session.proxies = proxies
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = ""

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

        # Configure the API base URL and headers
        self.base_url = "https://api.sambanova.ai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Any, Generator[Any, None, None]]:
        """Chat with AI using the Sambanova API."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {list(self.__available_optimizers)}"
                )

        payload = {
            "model": self.model,
            "stream": stream,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "max_tokens": self.max_tokens_to_sample,
        }

        def for_stream():
            streaming_text = ""
            try:
                response = self.session.post(
                    self.base_url, headers=self.headers, json=payload, stream=True, timeout=self.timeout
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Request failed: {response.status_code} - {response.text}"
                    )

                for line in response.iter_lines():
                    if line:
                        # Remove the "data:" prefix and extra whitespace if present
                        line_str = line.decode('utf-8').strip() if isinstance(line, bytes) else line.strip()
                        if line_str.startswith("data:"):
                            data = line_str[5:].strip()
                        else:
                            data = line_str
                        if data == "[DONE]":
                            break
                        try:
                            json_data = json.loads(data)
                            # Skip entries without valid choices
                            if not json_data.get("choices"):
                                continue
                            choice = json_data["choices"][0]
                            delta = choice.get("delta", {})
                            if "content" in delta:
                                content = delta["content"]
                                streaming_text += content
                                # Yield content directly as a string for consistency
                                yield content
                            # If finish_reason is provided, consider the stream complete
                            if choice.get("finish_reason"):
                                break
                        except json.JSONDecodeError:
                            continue
                self.last_response = streaming_text
                self.conversation.update_chat_history(
                    prompt, self.last_response
                )
            except requests.exceptions.RequestException as e:
                raise exceptions.ProviderConnectionError(f"Request failed: {e}")

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
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response `str`"""
        if stream:
            # For stream mode, yield the text chunks directly
            return self.ask(prompt, stream=True, optimizer=optimizer, conversationally=conversationally)
        else:
            # For non-stream mode, return the complete text response
            return self.ask(prompt, stream=False, optimizer=optimizer, conversationally=conversationally)

    def get_message(self, response: Any) -> str:
        """
        Retrieves a clean message from the provided response.

        Args:
            response: The raw response data.

        Returns:
            str: The extracted message.
        """
        if isinstance(response, str):
            return response
        elif isinstance(response, dict) and "text" in response:
            return response["text"]
        return ""

if __name__ == "__main__":
    from rich import print
    ai = Sambanova(api_key='')
    response = ai.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)