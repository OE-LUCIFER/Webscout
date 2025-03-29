import requests
import json
from typing import Union, Dict, Any

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions

class AI21(Provider):
    """
    A class to interact with the AI21 Studio API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "jamba-1.5-large",
        max_tokens: int = 1024,
        temperature: float = 0.4,
        top_p: float = 1,
        is_conversation: bool = True,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        system_prompt: str = "You are a helpful and informative AI assistant."
    ):
        """
        Initializes the AI21 Studio API with given parameters.
        """
        self.api_key = api_key
        self.api_endpoint = "https://api.ai21.com/studio/v1/chat/completions"
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.system_prompt = system_prompt
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json',
            'DNT': '1',
            'Origin': 'https://studio.ai21.com',
            'Referer': 'https://studio.ai21.com/',
            'Sec-CH-UA': '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
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

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        """
        Sends a prompt to the AI21 Studio API and returns the response.
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
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ],
            "n": 1,
            "max_tokens": self.max_tokens,
            "model": self.model,
            "stop": [],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "documents": [],
        }

        response = self.session.post(self.api_endpoint, headers=self.headers, json=payload, timeout=self.timeout)

        if not response.ok:
            raise exceptions.FailedToGenerateResponseError(
                f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
            )

        resp = response.json()
        self.last_response.update(resp)
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
        Generates a response from the AI21 API.
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
        """
        Extracts the message from the API response.
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response['choices'][0]['message']['content']

# Example usage
if __name__ == "__main__":
    from rich import print
    ai = AI21(api_key="api_key")
    response = ai.chat(input(">>> "))
    for line in response:
        print(line, end="", flush=True)
