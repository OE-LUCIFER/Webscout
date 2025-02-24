
import requests
import json
from typing import Any, Dict, Generator
from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.Litlogger import Logger, LogFormat
from webscout import LitAgent as Lit
class TextPollinationsAI(Provider):
    """
    A class to interact with the Pollinations AI API with comprehensive logging.
    """

    AVAILABLE_MODELS = [
        "openai", "openai-large", "qwen", "qwen-coder", "llama", "mistral",
        "unity", "midijourney", "rtist", "searchgpt", "evil", "deepseek",
        "claude-hybridspace", "deepseek-r1", "llamalight", "llamaguard",
        "gemini", "gemini-thinking", "hormoz"
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 8096,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "openai-large",
        system_prompt: str = "You are a helpful AI assistant.",
        logging: bool = False
    ):
        """Initializes the TextPollinationsAI API client with logging capabilities."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.logger = Logger(
            name="TextPollinationsAI",
            format=LogFormat.MODERN_EMOJI,
        ) if logging else None

        if self.logger:
            self.logger.info(f"Initializing TextPollinationsAI with model: {model}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://text.pollinations.ai/openai"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': Lit().random(),
            'Content-Type': 'application/json',
        }
        
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

        self.__available_optimizers = (
            method for method in dir(Optimizers)
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

        if self.logger:
            self.logger.info("TextPollinationsAI initialized successfully")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """Chat with AI with logging capabilities"""
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
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ],
            "model": self.model,
            "stream": stream,
        }

        def for_stream():
            if self.logger:
                self.logger.debug("Initiating streaming request to API")

            response = self.session.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=self.timeout
            )

            if not response.ok:
                if self.logger:
                    self.logger.error(f"API request failed. Status: {response.status_code}, Reason: {response.reason}")
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            if self.logger:
                self.logger.info(f"API connection established successfully. Status: {response.status_code}")

            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8').strip()
                    if line == "data: [DONE]":
                        if self.logger:
                            self.logger.debug("Stream completed")
                        break
                    if line.startswith('data: '):
                        try:
                            json_data = json.loads(line[6:])
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                choice = json_data['choices'][0]
                                if 'delta' in choice and 'content' in choice['delta']:
                                    content = choice['delta']['content']
                                else:
                                    content = ""
                                full_response += content
                                yield content if raw else dict(text=content)
                        except json.JSONDecodeError as e:
                            if self.logger:
                                self.logger.error(f"JSON parsing error: {str(e)}")
                            continue

            self.last_response.update(dict(text=full_response))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

            if self.logger:
                self.logger.debug("Response processing completed")

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
    ) -> str | Generator[str, None, None]:
        """Generate response as a string with logging"""
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
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    # Enable logging for testing
    ai = TextPollinationsAI(model="deepseek-r1", logging=True)
    response = ai.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)

