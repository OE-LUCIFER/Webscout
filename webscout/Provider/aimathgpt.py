import requests
import json
import os
from typing import Any, Dict, Optional, Generator, List, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions


class AIMathGPT(Provider):
    """
    A class to interact with the AIMathGPT API.
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
        model: str = "llama3",  # Default model
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """
        Initializes the AIMathGPT API with the given parameters.
        """
        self.url = "https://aimathgpt.forit.ai/api/ai"
        self.headers = {
            "authority": "aimathgpt.forit.ai",
            "method": "POST",
            "path": "/api/ai",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "cookie": (
                "NEXT_LOCALE=en; _ga=GA1.1.1515823701.1726936796; "
                "_ga_1F3ZVN96B1=GS1.1.1726936795.1.1.1726936833.0.0.0"
            ),
            "dnt": "1",
            "origin": "https://aimathgpt.forit.ai",
            "priority": "u=1, i",
            "referer": "https://aimathgpt.forit.ai/?ref=taaft&utm_source=taaft&utm_medium=referral",
            "sec-ch-ua": (
                "\"Microsoft Edge\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\""
            ),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
            ),
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
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
    ) -> Union[Dict, Generator]:
        """Sends a chat completion request to the AIMathGPT API."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)

        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")


        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "model": self.model,
        }


        def for_stream():
            try:
                with requests.post(self.url, headers=self.headers, data=json.dumps(payload), stream=True, timeout=self.timeout) as response:
                    if response.status_code != 200:
                        raise exceptions.FailedToGenerateResponseError(f"Request failed with status code {response.status_code}: {response.text}")

                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            try:
                                data = json.loads(line)
                                if 'result' in data and 'response' in data['result']:
                                    content = data['result']['response']
                                    streaming_text += content
                                    resp = dict(text=content)  # Yield only the new content
                                    yield resp if raw else resp
                                else:
                                    pass
                            except json.JSONDecodeError:
                                pass
                    self.conversation.update_chat_history(prompt, streaming_text)
                    self.last_response.update({"text": streaming_text})
            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")

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
    ) -> Union[str, Generator]:

        def for_stream():
            for response in self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt, stream=False, optimizer=optimizer, conversationally=conversationally
                )
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]


if __name__ == "__main__":
    from rich import print
    bot = AIMathGPT()
    try:
        response = bot.chat("What is the capital of France?", stream=True)
        for chunk in response:
            print(chunk, end="", flush=True)
    except Exception as e:
        print(f"An error occurred: {e}")
