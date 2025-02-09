import requests

from typing import Any, Dict, Optional, Generator, Union

from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.litagent import LitAgent


class Netwrck(Provider):
    """
    A class to interact with the Netwrck.com API. Supports streaming.
    """

    greeting = """An unknown multiverse phenomenon occurred, and you found yourself in a dark space. You looked around and found a source of light in a distance. You approached the light and *whoosh*....\nChoose your origin:\na) As a baby who just got birthed, your fate unknown\nb) As an amnesic stranded on an uninhabited island with mysterious ruins\nc) As an abandoned product of a forbidden experiment\nd) As a slave being sold at an auction\ne) Extremely Chaotic Randomizer\nOr, dive into your own fantasy."""

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
        model: str = "claude",
        is_conversation: bool = True,
        max_tokens: int = 2048,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = False,
        proxies: Optional[dict] = None,
        history_offset: int = 0,
        act: Optional[str] = None,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        top_p: float = 0.8,
        logging: bool = False,
    ):
        """Initializes the Netwrck API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {list(self.AVAILABLE_MODELS.keys())}"
            )

        self.model = model
        self.model_name = self.AVAILABLE_MODELS[model]
        self.system_prompt = system_prompt
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response: Dict[str, Any] = {}
        self.temperature = temperature
        self.top_p = top_p

        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()

        self.headers = {
            "authority": "netwrck.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://netwrck.com",
            "referer": "https://netwrck.com/",
            "user-agent": self.agent.random(),
        }
        self.session.headers.update(self.headers)
        self.proxies = proxies or {}

        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation, max_tokens, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        # Initialize logger
        self.logger = (
            LitLogger(
                name="Netwrck",
                format=LogFormat.MODERN_EMOJI,
                color_scheme=ColorScheme.CYBERPUNK,
            )
            if logging
            else None
        )

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        """Sends a prompt to the Netwrck API and returns the response."""

        if self.logger:
            self.logger.debug(f"ask() called with prompt: {prompt}")

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                if self.logger:
                    self.logger.error(f"Invalid optimizer: {optimizer}")
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )
        payload = {
            "query": prompt,
            "context": self.system_prompt,
            "examples": [],
            "model_name": self.model_name,
            "greeting": self.greeting,
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

                # Initialize an empty string to accumulate the streaming text
                streaming_text = ""
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8").strip('"')
                        streaming_text += decoded_line  # Accumulate the text
                        yield {"text": decoded_line}  # Yield each chunk

                # Optionally, you can update the conversation history with the full streaming text
                self.conversation.update_chat_history(payload["query"], streaming_text)

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error communicating with Netwrck: {e}")
                raise exceptions.ProviderConnectionError(
                    f"Error communicating with Netwrck: {e}"
                ) from e

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error communicating with Netwrck: {e}")
                raise exceptions.ProviderConnectionError(
                    f"Error communicating with Netwrck: {e}"
                ) from e

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
                # print(response.text)
                text = response.text.strip('"')
                self.last_response = {"text": text}
                self.conversation.update_chat_history(prompt, text)

                return self.last_response
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error communicating with Netwrck: {e}")
                raise exceptions.ProviderConnectionError(
                    f"Error communicating with Netwrck: {e}"
                ) from e

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> str:
        """Generates a response from the Netwrck API."""
        if self.logger:
            self.logger.debug(f"chat() called with prompt: {prompt}")

        def for_stream():
            for response in self.ask(
                prompt,
                stream=True,
                optimizer=optimizer,
                conversationally=conversationally,
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
    netwrck = Netwrck(model="claude", logging=True)
    response = netwrck.chat("tell me about Russia")
    print(response)

    # Streaming example
    print("\nStreaming Response:")
    response = netwrck.chat("tell me about India", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
    print()  # Add a newline at the end
