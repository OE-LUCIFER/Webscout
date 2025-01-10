import requests
import json
import os
from typing import Any, Dict, Optional, Generator, List, Union
import uuid

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions

from webscout import LitAgent
class GaurishCerebras(Provider):
    """
    A class to interact with the Gaurish Cerebras API.
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
        system_prompt: str = "You are a helpful assistant.", 
    ):
        """Initializes the Gaurish Cerebras API client."""
        self.url = "https://proxy.gaurish.xyz/api/cerebras/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "access-control-allow-credentials": "true",
            "access-control-allow-headers": "*",
            "access-control-allow-methods": "*",
            "access-control-allow-origin": "*",
            "cache-control": "public, max-age=0, must-revalidate",
            "referrer-policy": "strict-origin-when-cross-origin",
            "content-type": "text/event-stream; charset=utf-8",
            "strict-transport-security": "max-age=3600; includeSubDomains",
            "x-content-type-options": "nosniff",
            "x-matched-path": "/api/cerebras/[...path]",
            "x-ratelimit-limit-requests-day": "30000",
            "x-ratelimit-limit-tokens-minute": "60000",
            "x-ratelimit-remaining-requests-day": "29984",
            "x-ratelimit-remaining-tokens-minute": "60000",
            "x-ratelimit-reset-requests-day": "24092.23299384117",
            "x-ratelimit-reset-tokens-minute": "32.232993841171265",
            "x-request-id": "0vWYzSEvd9Ytk5Zvl8NGRfT_Ekjm0ErInwwxlihBPyqUBAjJpyXwCg==",
            "x-vercel-id": "bom1::nsbfd-1729703907288-16e74bb1db50",
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "dnt": "1",
            "origin": "https://chat.gaurish.xyz",
            "priority": "u=1, i",
            "referer": "https://chat.gaurish.xyz/",
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Microsoft Edge\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": LitAgent().random(),
            "x-stainless-arch": "unknown",
            "x-stainless-lang": "js",
            "x-stainless-os": "Unknown",
            "x-stainless-package-version": "4.67.3",
            "x-stainless-retry-count": "0",
            "x-stainless-runtime": "browser:chrome",
            "x-stainless-runtime-version": "130.0.0",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.last_response = {}

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
            else intro or system_prompt or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.system_prompt = system_prompt  # Store the system prompt


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

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "model": "llama3.1-70b",
            "temperature": 0.75,
            "stream": stream,
        }

        def for_stream():
            try:
                with self.session.post(self.url, headers=self.headers, data=json.dumps(payload), stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()
                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            line = line.strip()
                            if line.startswith("data: "):
                                line = line[6:]
                                if line == "[DONE]":
                                    break
                                try:
                                    data = json.loads(line)
                                    if "choices" in data and data["choices"][0]["delta"].get("content"):
                                        content = data["choices"][0]["delta"]["content"]
                                        streaming_text += content
                                        resp = dict(text=content)  # Yield only the new content
                                        yield resp if raw else resp
                                except json.JSONDecodeError:
                                    # print(f"[Warning] Invalid JSON chunk received: {line}")
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
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]



if __name__ == "__main__":
    from rich import print
    bot = GaurishCerebras()
    try:
        response = bot.chat("What is the capital of France?", stream=True)
        for chunk in response:
            print(chunk, end="", flush=True)
    except Exception as e:
        print(f"An error occurred: {e}")
