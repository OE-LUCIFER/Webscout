import requests
import json
import uuid

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions

class MemFree(Provider):
    """
    A class to interact with the MemFree.me API.
    """

    AVAILABLE_MODELS = [
        "gpt-4o-mini",
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
        model: str = "gpt-4o-mini",  # Default model
        system_prompt: str = "You are a helpful assistant.",
    ):
        """
        Initializes the MemFree.me API with given parameters.

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): HTTP request proxies in the format:
                                      `{"http": "http://proxy_host:proxy_port", "https": "https://proxy_host:proxy_port"}`.
                                      Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): AI model to use. Defaults to "gpt-4o-mini".
            system_prompt (str, optional): System prompt for MemFree. 
                                   Defaults to "You are a helpful assistant.".
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = 'https://www.memfree.me/api/search'
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.proxies = proxies # Store proxies for later use
        self.headers = {
            "Accept": "text/event-stream, text/event-stream",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://www.memfree.me",
            "Priority": "u=1, i",
            "Referer": "https://www.memfree.me/",
            "Sec-CH-UA": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
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
        # self.session.proxies = proxies - Removed to pass proxies in request method

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with MemFree

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
            "model": self.model,
            "source": "all",
            "profile": "",
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "id": str(uuid.uuid4()), 
                    "content": conversation_prompt,
                    "role": "user",
                    "attachments": []
                }
            ]
        }

        def for_stream():
            try:
                # Initiate the POST request with streaming enabled and proxies
                with requests.post(self.api_endpoint, headers=self.headers, data=json.dumps(payload), stream=True, timeout=self.timeout, proxies=self.proxies) as response:
                    if response.status_code != 200:
                        raise exceptions.FailedToGenerateResponseError(f"Request failed with status code: {response.status_code}")

                    # Iterate over each line in the streamed response
                    full_response = ''
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            decoded_line = line.strip() 
                            # Check if the line starts with 'data:'
                            if decoded_line.startswith("data:"):
                                # Extract the JSON part after 'data:'
                                json_data = decoded_line[5:].strip()
                                try:
                                    data = json.loads(json_data)
                                    # Print only if 'answer' key is present
                                    if "answer" in data:
                                        full_response += data["answer"]
                                        yield data["answer"] if raw else dict(text=full_response)
                                except json.JSONDecodeError:
                                    # Handle lines that are not valid JSON
                                    continue
                self.last_response.update(dict(text=full_response))
                self.conversation.update_chat_history(
                    prompt, self.get_message(self.last_response)
                )
            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"An error occurred while making the request: {e}")
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

if __name__ == "__main__":
    from rich import print

    ai = MemFree()
    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)