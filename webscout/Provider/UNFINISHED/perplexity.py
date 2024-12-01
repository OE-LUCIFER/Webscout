import json
import random
import requests
import websocket
from typing import List, Dict, Generator, Union, Optional

API_URL = "https://www.perplexity.ai/socket.io/"
WS_URL = "wss://www.perplexity.ai/socket.io/"

class PerplexityError(Exception):
    """Custom exception for Perplexity-related errors"""
    pass

class PerplexityLabs:
    url = "https://labs.perplexity.ai"
    working = True
    default_model = "llama-3.1-70b-instruct"
    
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

    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy
        self.session = requests.Session()
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
        
        try:
            self.session.get(self.url)
        except Exception as e:
            raise PerplexityError(f"Failed to initialize session: {str(e)}")

    def _get_session_id(self) -> str:
        t = format(random.getrandbits(32), "08x")
        try:
            response = self.session.get(
                f"{API_URL}?EIO=4&transport=polling&t={t}",
                proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None
            )
            response.raise_for_status()
            text = response.text
            
            if not text.startswith("0"):
                raise PerplexityError("Invalid response format")
            
            return json.loads(text[1:])["sid"]
        except requests.exceptions.RequestException as e:
            raise PerplexityError(f"Failed to get session ID: {str(e)}")
        except (json.JSONDecodeError, KeyError) as e:
            raise PerplexityError(f"Failed to parse session ID: {str(e)}")

    def _authenticate_session(self, sid: str, t: str) -> None:
        try:
            response = self.session.post(
                f"{API_URL}?EIO=4&transport=polling&t={t}&sid={sid}",
                data='40{"jwt":"anonymous-ask-user"}',
                proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None
            )
            response.raise_for_status()
            if response.text != "OK":
                raise PerplexityError("Authentication failed")
        except requests.exceptions.RequestException as e:
            raise PerplexityError(f"Authentication failed: {str(e)}")

    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[str, None, None]:
        """Generate responses from the model"""
        if model not in self.online_models + self.chat_models:
            raise PerplexityError(f"Invalid model: {model}")
            
        t = format(random.getrandbits(32), "08x")
        sid = self._get_session_id()
        self._authenticate_session(sid, t)

        ws = websocket.create_connection(
            f"{WS_URL}?EIO=4&transport=websocket&sid={sid}",
            header=[f"{k}: {v}" for k, v in self.headers.items()],
            cookie="; ".join([f"{k}={v}" for k, v in self.session.cookies.items()]),
            proxy=self.proxy
        )

        try:
            ws.send("2probe")
            if ws.recv() != "3probe":
                raise PerplexityError("WebSocket handshake failed")
            ws.send("5")
            ws.recv()
            ws.recv()

            message_data = {
                "version": "2.5",
                "source": "default",
                "model": model,
                "messages": messages
            }
            ws.send("42" + json.dumps(["perplexity_labs", message_data]))

            last_message = 0
            while True:
                message = ws.recv()
                if message == "2":
                    if last_message == 0:
                        raise PerplexityError("No response received")
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
                    raise PerplexityError(f"Failed to parse message: {str(e)}")

        finally:
            ws.close()

    def ask(self, question: str, model: str = None, stream: bool = False, system: str = None) -> Union[str, Generator[str, None, None]]:
        """Ask a single question and get a response"""
        model = model or self.default_model
        messages = []
        
        # Add system message if provided
        if system:
            messages.append({"role": "system", "content": system})
            
        # Add user message
        messages.append({"role": "user", "content": question})
        
        if stream:
            return self.generate(model, messages)
        return "".join(self.generate(model, messages))

    def chat(self, messages: List[Dict[str, str]], model: str = None, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """Have a multi-turn conversation with the model"""
        model = model or self.default_model
        
        # Validate message format
        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise PerplexityError("Each message must have 'role' and 'content' fields")
            if msg["role"] not in ["system", "assistant", "user"]:
                raise PerplexityError("Message role must be 'system', 'assistant', or 'user'")
        
        if stream:
            return self.generate(model, messages)
        return "".join(self.generate(model, messages))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'session'):
            self.session.close()


if __name__ == "__main__":
    # Example 1: Simple question with system prompt
    with PerplexityLabs() as perplexity:
        system_prompt = "You are a helpful AI assistant that specializes in explaining complex topics simply."
        response = perplexity.ask(
            "What is quantum computing?",
            model="llama-3.1-70b-instruct",
            system=system_prompt
        )
        print(f"Response with system prompt: {response}\n")

    # Example 2: Multi-turn conversation
    with PerplexityLabs() as perplexity:
        messages = [
            {
                "role": "system",
                "content": "You are a knowledgeable AI that provides real-time information."
            },
            {
                "role": "user",
                "content": "What are the latest developments in AI?"
            },
            {
                "role": "assistant",
                "content": "Some recent developments in AI include advancements in large language models..."
            },
            {
                "role": "user",
                "content": "Can you elaborate on language models?"
            }
        ]
        response = perplexity.chat(messages, model="llama-3.1-sonar-large-128k-online")
        print(f"Chat response: {response}")

    # Example 3: Streaming chat with roles
    with PerplexityLabs() as perplexity:
        messages = [
            {
                "role": "system",
                "content": "You are a creative storyteller."
            },
            {
                "role": "user",
                "content": "Tell me a short story about a space adventure."
            }
        ]
        print("Streaming story:")
        for chunk in perplexity.chat(messages, model="llama-3.1-70b-instruct", stream=True):
            print(chunk, end='', flush=True)
