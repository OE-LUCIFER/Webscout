from uuid import uuid4
from re import findall
import json

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from typing import Any, AsyncGenerator, Dict

import cloudscraper

class YouChat(Provider):
    """
    This class provides methods for interacting with the You.com chat API in a consistent provider structure.
    """

    AVAILABLE_MODELS = [
        "openai_o1",
        "openai_o1_mini",
        "gpt_4o_mini",
        "gpt_4o",
        "gpt_4_turbo",
        "gpt_4",
        "claude_3_5_sonnet",
        "claude_3_opus",
        "claude_3_sonnet",
        "claude_3_5_haiku",
        "claude_3_haiku",
        "llama3_3_70b",
        "llama3_2_90b",
        "llama3_2_11b",
        "llama3_1_405b",
        "llama3_1_70b",
        "llama3",
        "mistral_large_2",
        "gemini_1_5_flash",
        "gemini_1_5_pro",
        "databricks_dbrx_instruct",
        "qwen2p5_72b",
        "qwen2p5_coder_32b",
        "command_r",
        "command_r_plus",
        "solar_1_mini",
        "dolphin_2_5"
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
        model: str = "claude_3_5_haiku",  # Default model set to claude_3_5_haiku
    ):
        """Instantiates YouChat

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): Model to use. Defaults to "claude_3_5_haiku".
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = cloudscraper.create_scraper()  # Create a Cloudscraper session
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://you.com/api/streamingSearch"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
            "Accept": "text/event-stream",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Referer": "https://you.com/search?q=hi&fromSearchBar=true&tbm=youchat",
            "Connection": "keep-alive",
            "DNT": "1",
        }
        self.cookies = {
            "uuid_guest_backup": uuid4().hex,
            "youchat_personalization": "true",
            "youchat_smart_learn": "true",
            "youpro_subscription": "false",
            "ydc_stytch_session": uuid4().hex,
            "ydc_stytch_session_jwt": uuid4().hex,
            "__cf_bm": uuid4().hex,
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

        payload = {
                    "q": conversation_prompt,
                    "page": 2,
                    "count": 20,
                    "safeSearch": "Moderate",
                    "mkt": "en-IN",
                    "domain": "youchat",
                    "use_personalization_extraction": "false",
                    "queryTraceId": str(uuid4()),
                    "chatId": str(uuid4()),
                    "conversationTurnId": str(uuid4()),
                    "pastChatLength": 0,
                    "isSmallMediumDevice": "true",
                    "selectedChatMode": self.model,  # Use the selected model
                    "traceId": str(uuid4()),
                    "chat": "[]"
                }

        def for_stream():
            response = self.session.get(
                self.chat_endpoint, headers=self.headers, cookies=self.cookies, params=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_text = ""
            for value in response.iter_lines(
                decode_unicode=True,
                chunk_size=self.stream_chunk_size,
                delimiter="\n",
            ):
                try:
                    if bool(value) and value.startswith('data: ') and 'youChatToken' in value:
                        data = json.loads(value[6:])
                        token = data.get('youChatToken', '')
                        if token:
                            streaming_text += token
                            yield token if raw else dict(text=token)
                except json.decoder.JSONDecodeError:
                    pass
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
if __name__ == '__main__':
    from rich import print
    ai = YouChat(timeout=5000)
    response = ai.chat("hi", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
