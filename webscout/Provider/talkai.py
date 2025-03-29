import uuid
import cloudscraper
import json
from typing import Union, Any, Dict, Optional, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent

class Talkai(Provider):
    """
    A class to interact with the Talkai.info API.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2048,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "gpt-4o-mini",  # Default model
    ):
        """
        Initializes the Talkai.info API with given parameters.
        """
        self.session = cloudscraper.create_scraper()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://talkai.info/chat/send/"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.headers = {
            'Accept': 'application/json, text/event-stream',
            'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'Content-Type': 'application/json',
            'Origin': 'https://talkai.info',
            'Referer': 'https://talkai.info/chat/',
            'User-Agent': LitAgent().random(),
            'Cookie': '_csrf-front=e19e203a958c74e439261f6860535403324c9ab2ede76449e6407e54e1f366afa%3A2%3A%7Bi%3A0%3Bs%3A11%3A%22_csrf-front%22%3Bi%3A1%3Bs%3A32%3A%22QbnGY7XS5q9i3JnDvi6KRzrOk0D6XFnk%22%3B%7D; _ga=GA1.1.1383924142.1734246140; _ym_uid=1723397035198647017; _ym_d=1734246141; _ym_isad=1; _ym_visorc=b; talkai-front=ngbj23of1t0ujg2raoa3l57vqe; _ga_FB7V9WMN30=GS1.1.1734246139.1.1734246143.0.0.0'
        }
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
        self.session.proxies = proxies

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        """Chat with Talkai

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            dict: Response dictionary.
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(conversation_prompt if conversationally else prompt)
            else:
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        payload = {
            "type": "chat",
            "messagesHistory": [
                {
                    "id": str(uuid.uuid4()),
                    "from": "you",
                    "content": conversation_prompt
                }
            ],
            "settings": {
                "model": self.model
            }
        }

        def for_stream():
            try:
                with self.session.post(self.api_endpoint, headers=self.headers, json=payload, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()

                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if 'event: trylimit' in decoded_line:
                                break  # Stop if trylimit event is encountered
                            if decoded_line.startswith('data:'):
                                data = decoded_line[6:]  # Remove 'data: ' prefix
                                full_response += data
                                yield data if raw else dict(text=data)

                    self.last_response.update(dict(text=full_response))
                    self.conversation.update_chat_history(
                        prompt, self.get_message(self.last_response)
                    )

            except cloudscraper.exceptions as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")

        def for_non_stream():
            full_response = ""
            for line in for_stream():
                full_response += line['text'] if not raw else line
            return dict(text=full_response)

        return for_stream() if stream else for_non_stream()


    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
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

    def get_message(self, response: Dict[str, Any]) -> str:
        """Retrieves message only from response.

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted.
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')

if __name__ == "__main__":
    t = Talkai()
    resp = t.chat("write me about AI", stream=True)
    for chunk in resp:
        print(chunk, end="", flush=True)
