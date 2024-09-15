from typing import Any, Dict
import requests
import json
import re
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider
from webscout import exceptions


class Bing(Provider):
    """
    A class to interact with the Nexra Bing Chat API.
    """

    AVAILABLE_CONVERSATION_STYLES = [
        "Balanced",
        "Creative",
        "Precise",
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
        system_prompt: str = "You are a helpful AI assistant.",
        conversation_style: str = "Balanced",
    ):
        """
        Initializes the Nexra Bing Chat API with given parameters.
        """
        if conversation_style not in self.AVAILABLE_CONVERSATION_STYLES:
            raise ValueError(
                f"Invalid conversation_style: {conversation_style}. Choose from: {self.AVAILABLE_CONVERSATION_STYLES}"
            )

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://nexra.aryahcr.cc/api/chat/complements"
        self.stream_chunk_size = 1024

        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.conversation_style = conversation_style
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
    ) -> Dict[str, Any]:
        """Chat with AI"""
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
            "messages": messages,
            "conversation_style": self.conversation_style,
            "markdown": False,
            "stream": stream,
            "model": "Bing",
        }

        def for_stream():
            try:
                response = self.session.post(
                    self.api_endpoint, json=data, stream=True, timeout=self.timeout
                )
                response.raise_for_status()

                full_response = ""
                tmp = None
                for chunk in response.iter_content(chunk_size=self.stream_chunk_size):
                    if chunk:
                        chk = chunk.decode()
                        chk = chk.split(" ")

                        for data in chk:
                            result = None

                            try:
                                convert = json.loads(data)
                                result = data
                                tmp = None
                            except Exception as e:
                                if tmp is None:
                                    tmp = data
                                else:
                                    try:
                                        convert = json.loads(tmp)
                                        result = tmp
                                        tmp = None
                                    except Exception as e:
                                        tmp = tmp + data
                                        try:
                                            convert = json.loads(tmp)
                                            result = tmp
                                            tmp = None
                                        except Exception as e:
                                            tmp = tmp

                            if result is not None:
                                if "code" not in result and "status" not in result:
                                    full_response += result

                                    yield result if raw else dict(text=full_response)
                                else:
                                    raise exceptions.FailedToGenerateResponseError(result)
                self.last_response.update(dict(text=full_response))
                self.conversation.update_chat_history(
                    prompt, self.get_message(self.last_response)
                )
            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"An error occurred: {e}"
                )

        def for_non_stream():
            try:
                response = self.session.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=data,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                # Remove any leading non-printable characters
                clean_text = response.text.lstrip()

                # Attempt to parse the response as JSON
                resp = json.loads(clean_text)

                if "message" in resp:
                    self.last_response.update(dict(text=resp["message"]))
                    self.conversation.update_chat_history(
                        prompt, self.get_message(self.last_response)
                    )
                    return self.last_response
                else:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Unexpected response format: {clean_text}"
                    )

            except json.JSONDecodeError as e:
                # Handle JSON decoding error, print raw response for debugging
                print(f"Error decoding JSON. Raw response: {response.text}")
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to decode JSON response - {response.text}"
                ) from e
            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(
                    f"An error occurred: {e}"
                )

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """Generate response `str`"""

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
        assert isinstance(
            response, dict
        ), "Response should be of dict data-type only"
        text = re.sub(r"<sup>.*?</sup>", "", response["text"])
        return text

if __name__ == "__main__":
    from rich import print
    ai = Bing()
    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)