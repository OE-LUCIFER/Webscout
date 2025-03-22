import uuid
import requests
import json
import os
import re
from typing import Any, Dict, Optional, Generator, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from webscout import LitAgent

class Flowith(Provider):
    """
    A class to interact with the Flowith AI chat API.
    """

    AVAILABLE_MODELS = [
        "gpt-4o-mini",
        "deepseek-chat",
        "deepseek-reasoner",
        "claude-3.5-haiku",
        "llama-3.2-11b",
        "llama-3.2-90b",
        "gemini-2.0-flash",
        "o1",
        "o3-mini",
        "gpt-4o",
        "claude-3.5-sonnet",
        "gemini-2.0-pro",
        "claude-3.7-sonnet"

    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2048,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "claude-3.5-haiku"

    ):
        """Initializes the Flowith API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.url = "https://edge.flowith.net/ai/chat?mode=general"
        
        # Set up headers for the API request
        self.headers = {
            "authority": "edge.flowith.net",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "origin": "https://flowith.io",
            "referer": "https://edge.flowith.net/",
            "responsetype": "stream",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": LitAgent().random()  # Use LitAgent for user-agent
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.node_id = str(uuid.uuid4())  # Generate a new UUID for node ID

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

    def clean_response(self, text):
        """Remove text between <think> tags and other specific text patterns."""
        # Remove text between <think> tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

        return text.strip()

    def decode_response(self, content):
        """Try to decode the response content using multiple encodings."""
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        # If all encodings fail, try to decode with 'latin1' as it can decode any byte
        return content.decode('latin1')

    def ask(
        self,
        prompt: str,
        stream: bool = False,  # This parameter is kept for compatibility
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Dict[str, str]]:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        # Payload construction - using stream=False for simpler handling
        payload = {
            "model": self.model,
            "messages": [{"content": conversation_prompt, "role": "user"}],
            "stream": True,  # Set to False for direct response
            "nodeId": self.node_id
        }

        try:
            # Simple non-streaming request
            response = self.session.post(self.url, json=payload, timeout=self.timeout)
            
            if response.status_code != 200:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed with status code {response.status_code}"
                )
            
            # Get the response text using our multi-encoding decoder
            response_text = self.decode_response(response.content).strip()
            
            # Clean the response
            cleaned_text = self.clean_response(response_text)
            self.last_response = {"text": cleaned_text}
            
            # Update conversation history
            self.conversation.update_chat_history(prompt, cleaned_text)
            
            return {"text": cleaned_text}
                
        except requests.RequestException as e:
            raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

    def chat(
        self,
        prompt: str,
        stream: bool = False,  # Parameter kept for compatibility
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        # Always use non-streaming mode
        response = self.ask(prompt, False, optimizer=optimizer, conversationally=conversationally)
        return self.get_message(response)

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)
    
    for model in Flowith.AVAILABLE_MODELS:
        try:
            test_ai = Flowith(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word")
            response_text = response
            
            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Truncate response if too long
                display_text = response_text.strip()[:50] + "..." if len(response_text.strip()) > 50 else response_text.strip()
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"{model:<50} {'✗':<10} {str(e)}")