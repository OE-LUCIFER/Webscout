import requests
import json
import os
from typing import Any, Dict, Optional, Generator, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from webscout import LitAgent

class TwoAI(Provider):
    """
    A class to interact with the Two AI API with LitAgent user-agent.
    """

    AVAILABLE_MODELS = [
        "sutra-light",
    ]

    def __init__(
        self,
        api_key: str = None,
        is_conversation: bool = True,
        max_tokens: int = 1024,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "sutra-light",
        temperature: float = 0.6,
        system_message: str = "You are a helpful assistant."
    ):
        """Initializes the TwoAI API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
        self.url = "https://api.two.app/v1/sutra-light/completion"
        self.headers = {
            'User-Agent': LitAgent().random(),
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Session-Token': api_key,
            'Origin': 'https://chat.two.ai',
            'Referer': 'https://api.two.app/'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.system_message = system_message

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
        stream: bool = True,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        online_search: bool = True,
        reasoning_on: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        # Payload construction
        payload = {
            "messages": [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": conversation_prompt},
            ],
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens_to_sample,
            "reasoningOn": reasoning_on,
            "onlineSearch": online_search
        }

        def for_stream():
            try:
                with self.session.post(self.url, json=payload, stream=True, timeout=self.timeout) as response:
                    if response.status_code != 200:
                        raise exceptions.FailedToGenerateResponseError(
                            f"Request failed with status code {response.status_code}"
                        )
                    
                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            try:
                                chunk = json.loads(line)
                                if chunk["typeName"] == "LLMChunk":
                                    content = chunk["content"]
                                    streaming_text += content
                                    resp = dict(text=content)
                                    yield resp if raw else resp
                            except json.JSONDecodeError:
                                continue
                    
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)
                    
            except requests.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

        def for_non_stream():
            streaming_text = ""
            for resp in for_stream():
                streaming_text += resp["text"]
            self.last_response = {"text": streaming_text}
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = True,
        optimizer: str = None,
        conversationally: bool = False,
        online_search: bool = True,
        reasoning_on: bool = False,
    ) -> str:
        def for_stream():
            for response in self.ask(
                prompt, 
                True, 
                optimizer=optimizer, 
                conversationally=conversationally,
                online_search=online_search,
                reasoning_on=reasoning_on
            ):
                yield self.get_message(response)
        
        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt, 
                    False, 
                    optimizer=optimizer, 
                    conversationally=conversationally,
                    online_search=online_search,
                    reasoning_on=reasoning_on
                )
            )
        
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print

    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJNdTY3cGJQNENSVG1GVGVRS0dlcEtJeUthbWoxIiwic291cmNlIjoiRmlyZWJhc2UiLCJpYXQiOjE3NDExNjgxMTgsImV4cCI6MTc0MTE2OTAxOH0.7V6Ll9DInR5pe4WqsNkvlH3jzvYmSkPscm7diJuy6Zg"
    
    ai = TwoAI(
        api_key=api_key,
        timeout=60,
        system_message="You are an intelligent AI assistant. Be concise and helpful."
    )
    
    response = ai.chat("666+444=?", stream=True, reasoning_on=True)
    for chunk in response:
        print(chunk, end="", flush=True)
