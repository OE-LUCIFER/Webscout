import requests
import json
import uuid
import sys
from typing import Any, Dict, Optional, Generator, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from webscout import LitAgent

class HeckAI(Provider):
    """
    A class to interact with the HeckAI API with LitAgent user-agent.
    """

    AVAILABLE_MODELS = [
        "deepseek/deepseek-chat",
        "openai/gpt-4o-mini",
        "deepseek/deepseek-r1",
        "google/gemini-2.0-flash-001"
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "google/gemini-2.0-flash-001",
        language: str = "English"
    ):
        """Initializes the HeckAI API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.url = "https://api.heckai.weight-wave.com/api/ha/v1/chat"
        self.session_id = str(uuid.uuid4())
        self.language = language
        
        # Use LitAgent for user-agent
        self.headers = {
            'User-Agent': LitAgent().random(),
            'Content-Type': 'application/json',
            'Origin': 'https://heck.ai',
            'Referer': 'https://heck.ai/',
            'Connection': 'keep-alive'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.previous_question = None
        self.previous_answer = None

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
            "model": self.model,
            "question": conversation_prompt,
            "language": self.language,
            "sessionId": self.session_id,
            "previousQuestion": self.previous_question,
            "previousAnswer": self.previous_answer,
            "imgUrls": []
        }
        
        # Store this message as previous for next request
        self.previous_question = conversation_prompt

        def for_stream():
            try:
                with requests.post(self.url, headers=self.headers, data=json.dumps(payload), stream=True, timeout=self.timeout) as response:
                    if response.status_code != 200:
                        raise exceptions.FailedToGenerateResponseError(
                            f"Request failed with status code {response.status_code}"
                        )
                    
                    streaming_text = ""
                    in_answer = False
                    
                    for line in response.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                            
                        # Remove "data: " prefix
                        if line.startswith("data: "):
                            data = line[6:]
                        else:
                            continue
                        
                        # Check for control markers
                        if data == "[ANSWER_START]":
                            in_answer = True
                            continue
                            
                        if data == "[ANSWER_DONE]":
                            in_answer = False
                            continue
                            
                        if data == "[RELATE_Q_START]" or data == "[RELATE_Q_DONE]":
                            continue
                            
                        # Process content if we're in an answer section
                        if in_answer:
                            streaming_text += data
                            resp = dict(text=data)
                            yield resp if raw else resp
                    
                    self.previous_answer = streaming_text
                    self.conversation.update_chat_history(prompt, streaming_text)
                    
            except requests.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

        def for_non_stream():
            full_text = ""
            for chunk in for_stream():
                if isinstance(chunk, dict) and "text" in chunk:
                    full_text += chunk["text"]
            self.last_response = {"text": full_text}
            return self.last_response

        return for_stream() if stream else for_non_stream()

    @staticmethod
    def fix_encoding(text):
        if isinstance(text, dict) and "text" in text:
            try:
                text["text"] = text["text"].encode("latin1").decode("utf-8")
                return text
            except (UnicodeError, AttributeError) as e:
                return text
        elif isinstance(text, str):
            try:
                return text.encode("latin1").decode("utf-8")
            except (UnicodeError, AttributeError) as e:
                return text
        return text

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
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
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in HeckAI.AVAILABLE_MODELS:
        try:
            test_ai = HeckAI(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            for chunk in response:
                response_text += chunk
                print(f"\r{model:<50} {'Testing...':<10}", end="", flush=True)
            
            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Truncate response if too long
                display_text = response_text.strip()[:50] + "..." if len(response_text.strip()) > 50 else response_text.strip()
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")