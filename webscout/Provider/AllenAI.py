import requests
import json
import os
from uuid import uuid4
from typing import Any, Dict, Optional, Generator, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from webscout import LitAgent

class AllenAI(Provider):
    """
    A class to interact with the AllenAI (Ai2 Playground) API.
    """

    AVAILABLE_MODELS = [
        'tulu3-405b',
        # 'OLMo-2-1124-13B-Instruct',
        # 'tulu-3-1-8b',
        # 'Llama-3-1-Tulu-3-70B',
        # 'olmoe-0125'
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
        model: str = "tulu3-405b",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """Initializes the AllenAI API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.url = "https://playground.allenai.org"
        self.api_endpoint = "https://olmo-api.allen.ai/v4/message/stream"
        
        # Use LitAgent for user-agent
        self.headers = {
            'User-Agent': LitAgent().random(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': self.url,
            'Referer': f"{self.url}/",
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.model = model
        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}       
        # Generate user ID if needed
        self.x_anonymous_user_id = str(uuid4())
        self.parent = None

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

    def format_prompt(self, messages):
        """Format messages into a prompt string"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                formatted.append(f"System: {content}")
            elif role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")
        return "\n".join(formatted)

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        host: str = "inferd",
        private: bool = True,
        top_p: float = None,
        temperature: float = None,
    ) -> Union[Dict[str, Any], Generator]:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        # Generate boundary for multipart form
        boundary = f"----WebKitFormBoundary{uuid4().hex}"
        
        # Set content-type header for this specific request
        self.session.headers.update({
            "content-type": f"multipart/form-data; boundary={boundary}",
            "x-anonymous-user-id": self.x_anonymous_user_id
        })
        
        # Format messages for AllenAI
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": conversation_prompt}
        ]
        
        # Build multipart form data
        form_data = [
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="model"\r\n\r\n{self.model}\r\n',
            
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="host"\r\n\r\n{host}\r\n',
            
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="content"\r\n\r\n{self.format_prompt(messages)}\r\n',
            
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="private"\r\n\r\n{str(private).lower()}\r\n'
        ]
        
        # Add parent if exists
        if self.parent:
            form_data.append(
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="parent"\r\n\r\n{self.parent}\r\n'
            )
        
        # Add optional parameters
        if temperature is not None:
            form_data.append(
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="temperature"\r\n\r\n{temperature}\r\n'
            )
        
        if top_p is not None:
            form_data.append(
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="top_p"\r\n\r\n{top_p}\r\n'
            )
        
        form_data.append(f'--{boundary}--\r\n')
        data = "".join(form_data).encode()

        def for_stream():
            nonlocal data  # Explicitly capture the data variable from outer scope
            try:
                response = self.session.post(
                    self.api_endpoint,
                    data=data,
                    stream=True,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Request failed with status code {response.status_code}: {response.text}"
                    )
                
                streaming_text = ""
                current_parent = None
                
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=False):
                    if not chunk:
                        continue
                        
                    decoded = chunk.decode(errors="ignore")
                    for line in decoded.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        
                        if isinstance(data, dict):
                            # Update the parent ID
                            if data.get("children"):
                                for child in data["children"]:
                                    if child.get("role") == "assistant":
                                        current_parent = child.get("id")
                                        break
                            
                            # Process content
                            if "message" in data and data.get("content"):
                                content = data["content"]
                                if content.strip():
                                    streaming_text += content
                                    resp = dict(text=content)
                                    yield resp if raw else resp
                            
                            # Handle completion
                            if data.get("final") or data.get("finish_reason") == "stop":
                                if current_parent:
                                    self.parent = current_parent
                                
                                # Update conversation history
                                self.conversation.update_chat_history(prompt, streaming_text)
                                self.last_response = {"text": streaming_text}
                                return
                
            except requests.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

        def for_non_stream():
            streaming_text = ""
            for resp in for_stream():
                streaming_text += resp["text"]
            self.last_response = {"text": streaming_text}
            return self.last_response

        return for_stream() if stream else for_non_stream()

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

    for model in AllenAI.AVAILABLE_MODELS:
        try:
            test_ai = AllenAI(model=model, timeout=60)
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