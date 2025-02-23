
import requests
import json

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent as Lit
from webscout.Litlogger import Logger, LogFormat

class LlamaTutor(Provider):
    """
    A class to interact with the LlamaTutor API (Together.ai) with comprehensive logging.
    """

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
        system_prompt: str = "You are a helpful AI assistant.",
        logging: bool = False
    ):
        """
        Initializes the LlamaTutor API with given parameters and logging capabilities.
        """
        self.logger = Logger(
            name="LlamaTutor",
            format=LogFormat.MODERN_EMOJI,

        ) if logging else None

        if self.logger:
            self.logger.info("Initializing LlamaTutor API")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://llamatutor.together.ai/api/getChat"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "DNT": "1",
            "Origin": "https://llamatutor.together.ai",
            "Referer": "https://llamatutor.together.ai/",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": Lit().random(),
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        
        self.session.headers.update(self.headers)
        
        if self.logger:
            self.logger.debug("Headers configured and session updated")

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

        if self.logger:
            self.logger.info("LlamaTutor initialized successfully")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with LlamaTutor with logging capabilities"""
        if self.logger:
            self.logger.debug(f"Processing request - Prompt: {prompt[:50]}...")
            self.logger.debug(f"Stream: {stream}, Optimizer: {optimizer}")

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
                if self.logger:
                    self.logger.debug(f"Applied optimizer: {optimizer}")
            else:
                if self.logger:
                    self.logger.error(f"Invalid optimizer requested: {optimizer}")
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": conversation_prompt
                }
            ]
        }

        def for_stream():
            try:
                if self.logger:
                    self.logger.debug("Initiating streaming request to API")

                response = requests.post(
                    self.api_endpoint,
                    headers=self.headers,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                if self.logger:
                    self.logger.info(f"API connection established successfully. Status: {response.status_code}")
                
                full_response = ''
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        try:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data: "):
                                json_data = json.loads(decoded_line[6:])
                                if "text" in json_data:
                                    full_response += json_data["text"]
                                    yield json_data["text"] if raw else dict(text=json_data["text"])
                        except json.JSONDecodeError as e:
                            if self.logger:
                                self.logger.warning(f"Failed to parse response line: {e}")
                            continue

                self.last_response.update(dict(text=full_response))
                self.conversation.update_chat_history(
                    prompt, self.get_message(self.last_response)
                )

            except requests.exceptions.HTTPError as http_err:
                if self.logger:
                    self.logger.error(f"HTTP error occurred: {http_err}")
                raise exceptions.FailedToGenerateResponseError(f"HTTP error occurred: {http_err}")
            except requests.exceptions.RequestException as err:
                if self.logger:
                    self.logger.error(f"Request error occurred: {err}")
                raise exceptions.FailedToGenerateResponseError(f"An error occurred: {err}")

        def for_non_stream():
            if self.logger:
                self.logger.debug("Processing non-streaming request")
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
        """Generate response with logging capabilities"""
        if self.logger:
            self.logger.debug(f"Chat request initiated - Prompt: {prompt[:50]}...")

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
        """Retrieves message from response with validation"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    # Enable logging for testing
    ai = LlamaTutor(logging=True)
    response = ai.chat("Write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)