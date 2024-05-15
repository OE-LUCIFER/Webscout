from poe_api_wrapper import PoeApi
from poe_api_wrapper.api import BOTS_LIST
from ..AIbase import Provider
from ..AIutel import Conversation
from ..AIutel  import Optimizers
from ..AIutel  import AwesomePrompts
from pathlib import Path
from json import loads
from json import dumps
from loguru import logger
import logging

logger.remove()


class POE(Provider):
    def __init__(
        self,
        cookie: str,
        model: str = "Assistant",
        proxy: bool = False,
        timeout: int = 30,
        filepath: str = None,
        update_file: str = True,
        intro: str = None,
        act: str = None,
        init: bool = True,
    ):
        """Initializes POE

        Args:
            cookie (str): Path to `poe.com.cookies.json` file or 'p-b' cookie-value.
            model (str, optional): Model name. Default to Assistant.
            proxy (bool, optional): Flag for Httpx request proxy. Defaults to False.
            timeout (int, optional): Http request timeout. Defaults to 30.
            filepath (str, optional): Path to save the chat history. Defaults to None.
            update_file (str, optional): Flag for controlling chat history updates. Defaults to True.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            init (bool, optional): Resend the intro prompt. Defaults to True.
        """
        assert isinstance(
            cookie, str
        ), f"Cookie must be of {str} datatype only not {type(cookie)}"
        assert (
            model in BOTS_LIST.keys()
        ), f"model name '{model}' is not one of {', '.join(list(BOTS_LIST.keys()))}"
        cookie_path = Path(cookie)

        if cookie_path.exists() or any(["/" in cookie, ".json" in cookie]):
            cookie = None
            all_cookies = loads(cookie_path.read_text())
            for entry in all_cookies:
                if entry["name"] == "p-b":
                    cookie = entry["value"]
            assert (
                cookie
            ), f'Required cookie value cannot be retrieved from the path  "{cookie_path.as_posix()}"'

        if proxy:
            import poe_api_wrapper.proxies as proxies

            proxies.PROXY = True

        self.bot = BOTS_LIST[model]
        self.session = PoeApi(cookie)
        self.last_response = {}
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
            status=False, filepath=filepath, update_file=update_file
        )
        if init:
            self.ask(self.conversation.intro)  # Init

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
                optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defeaults to None
                conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            Returns:
               dict : {}
        ```json
        {
            "id": "TWVzc2FnZToxMTU0MzgyNDQ1ODU=",
            "messageId": 115438244585,
            "creationTime": 1707777376544407,
            "clientNonce": null,
            "state": "complete",
            "text": "Hello! How can I assist you today?",
            "author": "capybara",
            "contentType": "text_markdown",
            "sourceType": "chat_input",
            "attachmentTruncationState": "not_truncated",
            "attachments": [],
            "vote": null,
            "suggestedReplies": [],
            "hasCitations": false,
            "__isNode": "Message",
            "textLengthOnCancellation": null,
            "chatCode": "21a2jn0yrq9phxiy478",
            "chatId": 328236777,
            "title": null,
            "response": ""
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

        def for_stream():
            for response in self.session.send_message(self.bot, conversation_prompt):
                if raw:
                    yield dumps(response)
                else:
                    yield response

                self.last_response.update(response)

            self.conversation.update_chat_history(
                prompt,
                self.get_message(self.last_response),
                force=True,
            )

        def for_non_stream():
            # let's make use of stream
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