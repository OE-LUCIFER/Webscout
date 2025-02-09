import cloudscraper
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions


class Editee(Provider):
    """
    A class to interact with the Editee.com API.
    """

    AVAILABLE_MODELS = [
        "gemini",  # it is gemini 1.5pro
        "claude",  # it is claude 3.5
        "gpt4",  # it is gpt4o
        "mistrallarge",  # it is mistral large2
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
        model: str = "mistrallarge",
    ) -> None:
        """
        Initializes the Editee API with given parameters.

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
            model (str, optional): AI model to use for text generation. Defaults to "gemini".
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}"
            )

        self.session = cloudscraper.create_scraper()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://editee.com/submit/chatgptfree"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self._sessionValue = self._get_session()
        self.headers = {
            "authority": "editee.com",
            "path": "/submit/chatgptfree",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "cookie": f"editeecom_session={self._sessionValue}",
            "origin": "https://editee.com",
            "referer": "https://editee.com/chat-gpt",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
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

    def _get_session(self):
        """Gets the editeecom_session value."""
        res = self.session.get("https://editee.com/chat-gpt")
        if res.cookies.get_dict():
            first_cookie_name, session_value = next(
                iter(res.cookies.get_dict().items())
            )
        return session_value

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

        payload = {
            "context": " ",
            "selected_model": self.model,
            "template_id": "",
            "user_input": conversation_prompt,
        }

        response = self.session.post(
            self.api_endpoint, headers=self.headers, json=payload, timeout=self.timeout
        )
        if not response.ok:
            raise exceptions.FailedToGenerateResponseError(
                f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
            )

        resp = response.json()
        self.last_response.update(dict(text=resp["text"]))
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
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
        """
        return self.get_message(
            self.ask(
                prompt,
                optimizer=optimizer,
                conversationally=conversationally,
            )
        )

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]


if __name__ == "__main__":
    from rich import print

    ai = Editee()
    response = ai.chat("tell me about india")
    for chunk in response:
        print(chunk, end="", flush=True)
