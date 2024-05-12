import requests
import json
import uuid
from typing import Any, Dict, Optional
from ..AIutel import Optimizers
from ..AIutel import Conversation
from ..AIutel import AwesomePrompts, sanitize_stream
from ..AIbase import Provider, AsyncProvider
from webscout import exceptions

class Berlin4h(Provider):
    """
    A class to interact with the Berlin4h AI API.
    """

    def __init__(
        self,
        api_token: str = "3bf369cd84339603f8a5361e964f9ebe",
        api_endpoint: str = "https://ai.berlin4h.top/api/chat/completions",
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.9,
        presence_penalty: float = 0,
        frequency_penalty: float = 0,
        max_tokens: int = 4000,
        is_conversation: bool = True,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ) -> None:
        """
        Initializes the Berlin4h API with given parameters.

        Args:
            api_token (str): The API token for authentication.
            api_endpoint (str): The API endpoint to use for requests.
            model (str): The AI model to use for text generation.
            temperature (float): The temperature parameter for the model.
            presence_penalty (float): The presence penalty parameter for the model.
            frequency_penalty (float): The frequency penalty parameter for the model.
            max_tokens (int): The maximum number of tokens to generate.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.api_token = api_token
        self.api_endpoint = api_endpoint
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.max_tokens = max_tokens
        self.parent_message_id: Optional[str] = None
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.stream_chunk_size = 1
        self.timeout = timeout
        self.last_response = {}
        self.headers = {"Content-Type": "application/json", "Token": self.api_token}
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
        Sends a prompt to the Berlin4h AI API and returns the response.

        Args:
            prompt: The text prompt to generate text from.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            raw (bool, optional): Whether to return the raw response. Defaults to False.
            optimizer (str, optional): The name of the optimizer to use. Defaults to None.
            conversationally (bool, optional): Whether to chat conversationally. Defaults to False.

        Returns:
            The response from the API.
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

        payload: Dict[str, any] = {
            "prompt": conversation_prompt,
            "parentMessageId": self.parent_message_id or str(uuid.uuid4()),
            "options": {
                "model": self.model,
                "temperature": self.temperature,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
                "max_tokens": self.max_tokens,
            },
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint, json=payload, headers=self.headers, stream=True, timeout=self.timeout
            )

            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason})"
                )

            streaming_response = ""
            # Collect the entire line before processing
            for line in response.iter_lines(decode_unicode=True): 
                if line:
                    try:
                        json_data = json.loads(line)
                        content = json_data['content']
                        if ">" in content: break
                        streaming_response += content
                        yield content if raw else dict(text=streaming_response)  # Yield accumulated response
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