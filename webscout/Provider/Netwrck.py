import requests
from typing import Any, Dict, Generator, Optional
from webscout.AIutel import Optimizers, Conversation
from webscout.AIbase import Provider
from webscout import exceptions

class Netwrck(Provider):
    """
    A class to interact with the Netwrck.com API. Supports streaming.
    """

    AVAILABLE_MODELS = {
        "lumimaid": "neversleep/llama-3.1-lumimaid-8b",
        "grok": "x-ai/grok-2",
        "claude": "anthropic/claude-3.5-sonnet:beta",
        "euryale": "sao10k/l3-euryale-70b",
        "gpt4mini": "openai/gpt-4o-mini",
        "mythomax": "gryphe/mythomax-l2-13b",
        "gemini": "google/gemini-pro-1.5",
        "lumimaid70b": "neversleep/llama-3.1-lumimaid-70b",
        "nemotron": "nvidia/llama-3.1-nemotron-70b-instruct",
    }

    def __init__(
        self,
        model: str = "lumimaid",
        is_conversation: bool = False,
        max_tokens: int = 2048,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = False,
        proxies: Optional[dict] = None,
        history_offset: int = 0,
        act: Optional[str] = None,
        system_prompt: str = "You are a helpful assistant.",
    ):
        """Initializes the Netwrck API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {list(self.AVAILABLE_MODELS.keys())}")

        self.model = model
        self.model_name = self.AVAILABLE_MODELS[model]
        self.system_prompt = system_prompt
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response: Dict[str, Any] = {}
        self.headers = {
            'authority': 'netwrck.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://netwrck.com',
            'referer': 'https://netwrck.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
        }
        self.session.headers.update(self.headers)
        self.proxies = proxies or {}
        self.conversation = Conversation(is_conversation, max_tokens, filepath, update_file)
        self.conversation.history_offset = history_offset
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        """Sends a prompt to the Netwrck API and returns the response."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        payload = {
            "query": conversation_prompt,
            "context": self.system_prompt,
            "examples": [],
            "model_name": self.model_name,
        }

        def for_stream():
            try:
                response = self.session.post(
                    "https://netwrck.com/api/chatpred_or",
                    json=payload,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=self.timeout,
                    stream=True,
                )
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8').strip('"')
                        result = {"text": decoded_line} if not raw else decoded_line
                        yield result
            except Exception as e:
                raise exceptions.ProviderConnectionError(f"Error communicating with Netwrck: {e}") from e

        def for_non_stream():
            try:
                response = self.session.post(
                    "https://netwrck.com/api/chatpred_or",
                    json=payload,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                text = response.text.strip('"')
                self.last_response = {"text": text}
                return self.last_response
            except Exception as e:
                raise exceptions.ProviderConnectionError(f"Error communicating with Netwrck: {e}") from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> str:
        """Generates a response from the Netwrck API."""
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
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

# Example Usage:
if __name__ == "__main__":
    from rich import print

    # Non-streaming example
    print("Non-Streaming Response:")
    netwrck = Netwrck(model="lumimaid")
    response = netwrck.chat("What is the capital of France?")
    print(response)

    # Streaming example
    print("\nStreaming Response:")
    response = netwrck.chat("tell me about india", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
    print()  # Add a newline at the end
