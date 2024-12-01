import requests
import json
from typing import Any, Dict, Optional, Generator, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions


class RoboCoders(Provider):
    """
    A class to interact with the RoboCoders API.
    """

    api_endpoint = "https://api.robocoders.ai/chat"
    working = True
    supports_message_history = True
    default_model = "GeneralCodingAgent"
    agent = [default_model, "RepoAgent", "FrontEndAgent"]
    models = [*agent]

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
        model: str = default_model,
        system_prompt: str = "You are a helpful coding assistant.",
    ):
        """Initializes the RoboCoders API client."""
        if model not in self.models:
            raise ValueError(f"Invalid model: {model}. Choose from: {', '.join(self.models)}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt

        self.headers = {"Content-Type": "application/json"}
        self.access_token = self._get_access_token()  # Get token on initialization
        if not self.access_token:
            raise exceptions.AuthenticationError("Failed to get access token")

        self.session_id = self._create_session()  # Create session on initialization
        if not self.session_id:
            raise exceptions.SessionCreationError("Failed to create session")

        self.headers["Authorization"] = f"Bearer {self.access_token}"

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

    def _get_access_token(self) -> Optional[str]:
        """Get access token for authentication."""
        url_auth = "https://api.robocoders.ai/auth"
        headers_auth = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        }
        try:
            response = self.session.get(url_auth, headers=headers_auth, timeout=self.timeout)
            response.raise_for_status() # Raise exception for HTTP errors
            text = response.text
            return text.split('id="token">')[1].split("</pre>")[0].strip()
        except (requests.exceptions.RequestException, IndexError) as e:
            raise exceptions.APIConnectionError(f"Failed to get access token: {e}")


    def _create_session(self) -> Optional[str]:
        """Create a new chat session."""
        url_create_session = "https://api.robocoders.ai/create-session"
        headers_create_session = {"Authorization": f"Bearer {self.access_token}"}
        try:
            response = self.session.get(url_create_session, headers=headers_create_session, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("sid")
        except requests.exceptions.RequestException as e:
            raise exceptions.APIConnectionError(f"Failed to create session: {e}")



    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict, Generator[str, None, None]]:
        """
        Sends a prompt to the RoboCoders API and returns the response.
        """
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

        data = {
            "sid": self.session_id,
            "prompt": conversation_prompt,
            "agent": self.model,
        }

        def generate_chunks():
            response = self._make_request(
                "POST", self.api_endpoint, headers=self.headers, json=data, stream=True
            )
            for line in response.iter_lines():
                if line:
                    try:
                        response_data = json.loads(line)
                        message = response_data.get("message", "")
                        if message:
                            yield message
                    except json.JSONDecodeError:
                        pass  # Handle or log the error as needed

        if stream:
            streaming_text = ""
            for chunk in generate_chunks():
                streaming_text += chunk
                yield chunk if raw else {"text": chunk}
            self.last_response.update({"text": streaming_text}) #Update last_response
            self.conversation.update_chat_history(prompt, streaming_text)
        else:
            full_response = "".join(generate_chunks())
            self.last_response.update({"text": full_response})
            self.conversation.update_chat_history(prompt, full_response)
            return self.last_response

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        try:
            response = self.session.request(
                method, url, timeout=self.timeout, **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise exceptions.APIConnectionError(f"Failed to make request: {e}") from e

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response string or stream."""

        if stream:
            gen = self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            )
            for chunk in gen:
                yield self.get_message(chunk)
        else:
            return self.get_message(
                self.ask(prompt, stream=False, optimizer=optimizer, conversationally=conversationally)
            )

    def get_message(self, response: Dict[str, Any]) -> str:
        """Retrieves message from response."""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]


if __name__ == "__main__":
    from rich import print
    ai = RoboCoders(model="GeneralCodingAgent")
    response = ai.chat("Can you help me with Python programming?", stream=True)
    for chunk in response:
        print(chunk, end='', flush=True)