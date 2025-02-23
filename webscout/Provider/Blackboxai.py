import requests
import json
from typing import Any, Dict, Optional, Union, Generator, List
from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.Litlogger import Logger, LogFormat

class BLACKBOXAI(Provider):
    """
    BlackboxAI provider for interacting with the Blackbox API.
    Supports synchronous operations with multiple models.
    """
    url = "https://api.blackbox.ai"
    api_endpoint = "https://api.blackbox.ai/api/chat"



    AVAILABLE_MODELS = {
        "deepseek-v3": "deepseek-ai/DeepSeek-V3",
        "deepseek-r1": "deepseek-ai/DeepSeek-R1",
        "deepseek-chat": "deepseek-ai/deepseek-llm-67b-chat",
        "mixtral-small-28b": "mistralai/Mistral-Small-24B-Instruct-2501",
        "dbrx-instruct": "databricks/dbrx-instruct",
        "qwq-32b": "Qwen/QwQ-32B-Preview",
        "hermes-2-dpo": "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
        "claude-3.5-sonnet": "claude-sonnet-3.5",
        "gemini-1.5-flash": "gemini-1.5-flash",
        "gemini-1.5-pro": "gemini-pro",
        "gemini-2.0-flash": "Gemini-Flash-2.0",
    }

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 8000,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "deepseek-ai/DeepSeek-V3",
        logging: bool = False,
        system_message: str = "You are a helpful AI assistant."
    ):
        """Initialize BlackboxAI with enhanced configuration options."""
        self.logger = Logger(
            name="BlackboxAI",
            format=LogFormat.MODERN_EMOJI,

        ) if logging else None

        self.session = requests.Session()
        self.max_tokens_to_sample = max_tokens
        self.is_conversation = is_conversation
        self.timeout = timeout
        self.last_response = {}
        self.model = self.get_model(model)
        self.system_message = system_message

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        if self.logger:
            self.logger.info(f"Initializing BlackboxAI with model: {self.model}")

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
        self.session.proxies = proxies

    @classmethod
    def get_model(self, model: str) -> str:
        """Resolve model name from alias"""
        if model in self.AVAILABLE_MODELS:
            return self.AVAILABLE_MODELS[model]
        raise ValueError(f"Unknown model: {model}. Available models: {', '.join(self.AVAILABLE_MODELS)}")

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> Generator[str, None, None]:
        """Make synchronous request to BlackboxAI API."""
        if self.logger:
            self.logger.debug(f"Making request with {len(messages)} messages")

        data = {
            "messages": messages,
            "model": self.model,
            "max_tokens": self.max_tokens_to_sample
        }

        try:
            response = self.session.post(
                self.api_endpoint,
                json=data,
                headers=self.headers,
                stream=stream,
                timeout=self.timeout
            )
            
            if not response.ok:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                if self.logger:
                    self.logger.error(error_msg)
                raise exceptions.FailedToGenerateResponseError(error_msg)

            if stream:
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        yield line
            else:
                yield response.text

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.error(f"Request failed: {str(e)}")
            raise exceptions.ProviderConnectionError(f"Connection error: {str(e)}")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, str], Generator[Dict[str, str], None, None]]:
        """Send a prompt to BlackboxAI API and return the response."""
        if self.logger:
            self.logger.debug(f"Processing request [stream={stream}]")

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
                    self.logger.error(f"Invalid optimizer: {optimizer}")
                raise ValueError(f"Optimizer is not one of {self.__available_optimizers}")

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": conversation_prompt}
        ]

        def for_stream():
            for text in self._make_request(messages, stream=True):
                yield {"text": text}

        def for_non_stream():
            response_text = next(self._make_request(messages, stream=False))
            self.last_response = {"text": response_text}
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response as string."""
        if self.logger:
            self.logger.debug(f"Chat request initiated [stream={stream}]")

        def for_stream():
            for response in self.ask(
                prompt,
                stream=True,
                optimizer=optimizer,
                conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt,
                    stream=False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Dict[str, Any]) -> str:
        """Extract message from response dictionary."""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')

if __name__ == "__main__":
    from rich import print
    
    # Example usage
    ai = BLACKBOXAI(model="deepseek-v3", logging=True)
    
    try:
        print("Non-streaming response:")
        response = ai.chat("What is quantum computing?")
        print(response)
    
    except Exception as e:
        print(f"Error: {str(e)}")
