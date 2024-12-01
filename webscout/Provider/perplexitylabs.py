import json
import random
import requests
import websocket
from typing import Generator, Union, Optional, Dict, Any

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions

API_URL = "https://www.perplexity.ai/socket.io/"
WS_URL = "wss://www.perplexity.ai/socket.io/"

class PerplexityLabs(Provider):
    """
    A class to interact with the Perplexity Labs API
    """
    url = "https://labs.perplexity.ai"

    # Models with web search capability
    online_models = [
        "llama-3.1-sonar-large-128k-online",
        "llama-3.1-sonar-small-128k-online",
    ]

    # Models for chat/instruct without web search
    chat_models = [
        "llama-3.1-sonar-large-128k-chat",
        "llama-3.1-sonar-small-128k-chat",
        "llama-3.1-8b-instruct",
        "llama-3.1-70b-instruct",
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
        model: str = "llama-3.1-sonar-large-128k-online",  
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """Initializes the PerplexityLabs API client."""
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": self.url,
            "Connection": "keep-alive",
            "Referer": f"{self.url}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
        self.session.headers.update(self.headers)
        self.proxies = proxies
        self.model = model
        self.conversation = Conversation(is_conversation, max_tokens, filepath, update_file)
        self.conversation.history_offset = history_offset
        self.__available_optimizers = ["gpt4", "claude", "gemini", "simple"]
        
        try:
            self.session.get(self.url)
        except requests.exceptions.RequestException as e:
            raise exceptions.ProviderConnectionError(f"Failed to initialize session: {e}")


    def _get_session_id(self) -> str:
        t = format(random.getrandbits(32), "08x")
        try:
            response = self.session.get(
                f"{API_URL}?EIO=4&transport=polling&t={t}",
                proxies=self.proxies
            )
            response.raise_for_status()
            text = response.text
            
            if not text.startswith("0"):
                raise exceptions.InvalidResponseError("Invalid response format")
            
            return json.loads(text[1:])["sid"]
        except requests.exceptions.RequestException as e:
            raise exceptions.ProviderConnectionError(f"Failed to get session ID: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise exceptions.InvalidResponseError(f"Failed to parse session ID: {e}")


    def _authenticate_session(self, sid: str, t: str) -> None:
        try:
            response = self.session.post(
                f"{API_URL}?EIO=4&transport=polling&t={t}&sid={sid}",
                data='40{"jwt":"anonymous-ask-user"}',
                proxies=self.proxies
            )
            response.raise_for_status()
            if response.text != "OK":
                raise exceptions.AuthenticationError("Authentication failed")
        except requests.exceptions.RequestException as e:
            raise exceptions.ProviderConnectionError(f"Authentication failed: {e}")


    def _websocket_interaction(
        self,
        sid: str,
        t: str,
        prompt: str,
        model: str
    ) -> Generator[str, None, None]:
        ws = websocket.create_connection(
            f"{WS_URL}?EIO=4&transport=websocket&sid={sid}",
            header=[f"{k}: {v}" for k, v in self.headers.items()],
            cookie="; ".join([f"{k}={v}" for k, v in self.session.cookies.items()]),
            proxy=self.proxies.get("http") or self.proxies.get("https") if self.proxies else None,
        )

        try:
            ws.send("2probe")
            if ws.recv() != "3probe":
                raise exceptions.ProviderConnectionError("WebSocket handshake failed")
            ws.send("5")
            ws.recv()
            ws.recv()

            message_data = {
                "version": "2.5",
                "source": "default",
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            }
            ws.send("42" + json.dumps(["perplexity_labs", message_data]))

            last_message = 0
            while True:
                message = ws.recv()
                if message == "2":
                    if last_message == 0:
                        raise exceptions.InvalidResponseError("No response received")
                    ws.send("3")
                    continue

                try:
                    data = json.loads(message[2:])[1]
                    new_content = data["output"][last_message:]
                    if new_content:
                        yield new_content
                    last_message = len(data["output"])
                    if data.get("final", False):
                        break
                except Exception as e:
                    raise exceptions.InvalidResponseError(f"Failed to parse message: {e}")

        finally:
            ws.close()

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """Ask a question and get a response."""
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

        t = format(random.getrandbits(32), "08x")
        sid = self._get_session_id()
        self._authenticate_session(sid, t)

        def for_stream():
            gen = self._websocket_interaction(sid, t, conversation_prompt, self.model)
            full_response = ""
            for chunk in gen:
                full_response += chunk
                response_dict = dict(text=chunk)
                self.last_response.update(response_dict)
                yield response_dict if not raw else chunk
            self.conversation.update_chat_history(prompt, full_response)
            
        def for_non_stream():
            full_response = "".join(self._websocket_interaction(sid, t, conversation_prompt, self.model))
            self.last_response.update({"text": full_response})
            self.conversation.update_chat_history(prompt, full_response)
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            Union[str, Generator[str, None, None]]: Response generated
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

    def get_message(self, response: Dict[str, Any]) -> str:
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

    ai = PerplexityLabs()
    response = ai.chat("Tell me about Abhay Koul (HelpingAI)", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)