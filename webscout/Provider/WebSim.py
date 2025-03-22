import requests
import json
import string
import random
from typing import Any, Dict, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions

class WebSim(Provider):
    """
    A class to interact with the WebSim API.
    """

    url = "https://websim.ai"
    chat_api_endpoint = "https://websim.ai/api/v1/inference/run_chat_completion"
    image_api_endpoint = "https://websim.ai/api/v1/inference/run_image_generation"

    image_models = ['flux']
    AVAILABLE_MODELS = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-flash', 'gemini-pro', 'gemini-flash-thinking'] + image_models

    @staticmethod
    def generate_project_id(for_image=False):
        """
        Generate a project ID in the appropriate format
        
        For chat: format like 'ke3_xh5gai3gjkmruomu'
        For image: format like 'kx0m131_rzz66qb2xoy7'
        """
        chars = string.ascii_lowercase + string.digits
        
        if for_image:
            first_part = ''.join(random.choices(chars, k=7))
            second_part = ''.join(random.choices(chars, k=12))
            return f"{first_part}_{second_part}"
        else:
            prefix = ''.join(random.choices(chars, k=3))
            suffix = ''.join(random.choices(chars, k=15))
            return f"{prefix}_{suffix}"

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
        model: str = 'gemini-1.5-pro',
        aspect_ratio: str = "1:1"
    ):
        """Initializes the WebSim API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'text/plain;charset=UTF-8',
            'origin': 'https://websim.ai',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'websim-flags;': ''
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.aspect_ratio = aspect_ratio

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
    ) -> Dict[str, Any]:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        is_image_request = self.model in self.image_models
        project_id = self.generate_project_id(for_image=is_image_request)

        if is_image_request:
            self.headers['referer'] = 'https://websim.ai/@ISWEARIAMNOTADDICTEDTOPILLOW/ai-image-prompt-generator'
            return self._handle_image_request(project_id, conversation_prompt)
        else:
            self.headers['referer'] = 'https://websim.ai/@ISWEARIAMNOTADDICTEDTOPILLOW/zelos-ai-assistant'
            return self._handle_chat_request(project_id, conversation_prompt)

    def _handle_image_request(self, project_id: str, prompt: str) -> Dict[str, Any]:
        try:
            data = {
                "project_id": project_id,
                "prompt": prompt,
                "aspect_ratio": self.aspect_ratio
            }
            response = self.session.post(
                self.image_api_endpoint,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            response_json = response.json()
            image_url = response_json.get("url")
            if image_url:
                self.last_response = {"text": image_url}
                self.conversation.update_chat_history(prompt, image_url)
                return {"text": image_url}
            raise exceptions.FailedToGenerateResponseError("No image URL found in response")
        except requests.RequestException as e:
            raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

    def _handle_chat_request(self, project_id: str, prompt: str) -> Dict[str, Any]:
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                data = {
                    "project_id": project_id,
                    "messages": [{"role": "user", "content": prompt}]
                }
                response = self.session.post(
                    self.chat_api_endpoint,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 429:
                    last_error = exceptions.FailedToGenerateResponseError(
                        f"Rate limit exceeded: {response.text}"
                    )
                    retry_count += 1
                    if retry_count < max_retries:
                        continue
                    raise last_error
                
                response.raise_for_status()
                response_json = response.json()
                content = response_json.get("content", "")
                
                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return {"text": content.strip()}
                
            except requests.RequestException as e:
                if "Rate limit exceeded" in str(e) and retry_count < max_retries:
                    retry_count += 1
                else:
                    raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")
        
        raise last_error or exceptions.FailedToGenerateResponseError("Max retries exceeded")

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        return self.get_message(
            self.ask(prompt, False, optimizer=optimizer, conversationally=conversationally)
        )

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in WebSim.AVAILABLE_MODELS:
        try:
            test_ai = WebSim(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word")
            
            if response and len(response.strip()) > 0:
                status = "✓"
                # Clean and truncate response
                clean_text = response.strip().encode('utf-8', errors='ignore').decode('utf-8')
                display_text = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}") 