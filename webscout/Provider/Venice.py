import requests
import json
from typing import Generator, Dict, Any, List, Union
from uuid import uuid4

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent

class Venice(Provider):
    """
    A class to interact with the Venice AI API.
    """
    
    AVAILABLE_MODELS = [
        "llama-3.3-70b",
        "llama-3.2-3b-akash",
        "qwen2dot5-coder-32b"


    ]
    
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2000,
        timeout: int = 30,
        temperature: float = 0.8,
        top_p: float = 0.9,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "llama-3.3-70b",
        system_prompt: str = "You are a helpful AI assistant."
    ):
        """Initialize Venice AI client"""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.api_endpoint = "https://venice.ai/api/inference/chat"
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.timeout = timeout
        self.model = model
        self.system_prompt = system_prompt
        self.last_response = {}
        
        # Headers for the request
        self.headers = {
            "User-Agent": LitAgent().random(),
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://venice.ai",
            "referer": "https://venice.ai/chat/",
            "sec-ch-ua": '"Google Chrome";v="133", "Chromium";v="133", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }
        
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        
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

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        # Payload construction
        payload = {
            "requestId": str(uuid4())[:7],
            "modelId": self.model,
            "prompt": [{"content": conversation_prompt, "role": "user"}],
            "systemPrompt": self.system_prompt,
            "conversationType": "text",
            "temperature": self.temperature,
            "webEnabled": True,
            "topP": self.top_p,
            "includeVeniceSystemPrompt": False,
            "isCharacter": False,
            "clientProcessingTime": 2000
        }

        def for_stream():
            try:
                with self.session.post(
                    self.api_endpoint, 
                    json=payload, 
                    stream=True, 
                    timeout=self.timeout
                ) as response:
                    if response.status_code != 200:
                        raise exceptions.FailedToGenerateResponseError(
                            f"Request failed with status code {response.status_code}"
                        )
                    
                    streaming_text = ""
                    for line in response.iter_lines():
                        if not line:
                            continue
                        
                        try:
                            # Decode bytes to string
                            line_data = line.decode('utf-8').strip()
                            if '"kind":"content"' in line_data:
                                data = json.loads(line_data)
                                if 'content' in data:
                                    content = data['content']
                                    streaming_text += content
                                    resp = dict(text=content)
                                    yield resp if raw else resp
                        except json.JSONDecodeError:
                            continue
                        except UnicodeDecodeError:
                            continue
                    
                    self.conversation.update_chat_history(prompt, streaming_text)
                    
            except requests.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

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
    ) -> Union[str, Generator]:
        def for_stream():
            for response in self.ask(prompt, True, optimizer=optimizer, conversationally=conversationally):
                yield self.get_message(response)
        def for_non_stream():
            return self.get_message(
                self.ask(prompt, False, optimizer=optimizer, conversationally=conversationally)
            )
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    
    # Initialize Venice AI
    ai = Venice(model="qwen2dot5-coder-32b", timeout=50)
    
    # Test chat with streaming
    response = ai.chat("Write a short story about an AI assistant", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
