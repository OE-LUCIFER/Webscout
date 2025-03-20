import requests
import json
import os
from typing import Any, Dict, Optional, Generator, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from webscout import LitAgent

class DeepInfra(Provider):
    """
    A class to interact with the DeepInfra API with LitAgent user-agent.
    """

    AVAILABLE_MODELS = [
        # "anthropic/claude-3-7-sonnet-latest",  # >>>> NOT WORKING
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "deepseek-ai/DeepSeek-R1-Turbo",
        "deepseek-ai/DeepSeek-V3",
        # "google/gemma-2-27b-it",  # >>>> NOT WORKING
        # "google/gemma-2-9b-it",  # >>>> NOT WORKING
        "google/gemma-3-27b-it",
        # "google/gemini-1.5-flash",  # >>>> NOT WORKING
        # "google/gemini-1.5-flash-8b",  # >>>> NOT WORKING
        # "google/gemini-2.0-flash-001",  # >>>> NOT WORKING
        # "Gryphe/MythoMax-L2-13b",  # >>>> NOT WORKING
        # "meta-llama/Llama-3.2-1B-Instruct",  # >>>> NOT WORKING
        # "meta-llama/Llama-3.2-3B-Instruct",  # >>>> NOT WORKING
        "meta-llama/Llama-3.2-90B-Vision-Instruct",
        "meta-llama/Llama-3.2-11B-Vision-Instruct",
        # "meta-llama/Meta-Llama-3-70B-Instruct",  # >>>> NOT WORKING
        # "meta-llama/Meta-Llama-3-8B-Instruct",  # >>>> NOT WORKING
        # "meta-llama/Meta-Llama-3.1-70B-Instruct",  # >>>> NOT WORKING
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        # "meta-llama/Meta-Llama-3.1-405B-Instruct",  # >>>> NOT WORKING
        "microsoft/phi-4",
        "microsoft/Phi-4-multimodal-instruct",
        "microsoft/WizardLM-2-8x22B",
        # "mistralai/Mixtral-8x7B-Instruct-v0.1",  # >>>> NOT WORKING
        # "mistralai/Mistral-7B-Instruct-v0.3",  # >>>> NOT WORKING
        # "mistralai/Mistral-Nemo-Instruct-2407",  # >>>> NOT WORKING
        "mistralai/Mistral-Small-24B-Instruct-2501",
        "nvidia/Llama-3.1-Nemotron-70B-Instruct",
        # "NousResearch/Hermes-3-Llama-3.1-405B",  # >>>> NOT WORKING
        # "NovaSky-AI/Sky-T1-32B-Preview",  # >>>> NOT WORKING
        "Qwen/QwQ-32B",
        # "Qwen/Qwen2.5-7B-Instruct",  # >>>> NOT WORKING
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        # "Sao10K/L3.1-70B-Euryale-v2.2",  # >>>> NOT WORKING
        # "Sao10K/L3.3-70B-Euryale-v2.3",  # >>>> NOT WORKING
        "meta-llama/Llama-3.3-70B-Instruct",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,  # Set a reasonable default
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        browser: str = "chrome"
    ):
        """Initializes the DeepInfra API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.url = "https://api.deepinfra.com/v1/openai/chat/completions"
        
        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()
        # Use fingerprinting to create a consistent browser identity
        self.fingerprint = self.agent.generate_fingerprint(browser)
        
        # Use the fingerprint for headers
        self.headers = {
            "Accept": self.fingerprint["accept"],
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Origin": "https://deepinfra.com",
            "Pragma": "no-cache",
            "Referer": "https://deepinfra.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "X-Deepinfra-Source": "web-embed",
            "Sec-CH-UA": self.fingerprint["sec_ch_ua"] or '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self.fingerprint["platform"]}"',
            "User-Agent": self.fingerprint["user_agent"],
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model

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

    def refresh_identity(self, browser: str = None):
        """
        Refreshes the browser identity fingerprint.
        
        Args:
            browser: Specific browser to use for the new fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)
        
        # Update headers with new fingerprint
        self.headers.update({
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "Sec-CH-UA": self.fingerprint["sec_ch_ua"] or self.headers["Sec-CH-UA"],
            "Sec-CH-UA-Platform": f'"{self.fingerprint["platform"]}"',
            "User-Agent": self.fingerprint["user_agent"],
        })
        
        # Update session headers
        for header, value in self.headers.items():
            self.session.headers[header] = value
        
        return self.fingerprint

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
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream
        }

        def for_stream():
            try:
                with requests.post(self.url, headers=self.headers, data=json.dumps(payload), stream=True, timeout=self.timeout) as response:
                    if response.status_code != 200:
                        raise exceptions.FailedToGenerateResponseError(
                            f"Request failed with status code {response.status_code}"
                        )
                    
                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            line = line.strip()
                            if line.startswith("data: "):
                                json_str = line[6:]
                                if json_str == "[DONE]":
                                    break
                                try:
                                    json_data = json.loads(json_str)
                                    if 'choices' in json_data:
                                        choice = json_data['choices'][0]
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            content = choice['delta']['content']
                                            streaming_text += content
                                            resp = dict(text=content)
                                            yield resp if raw else resp
                                except json.JSONDecodeError:
                                    continue
                    
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)
                    
            except requests.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

        def for_non_stream():
            try:
                response = requests.post(self.url, headers=self.headers, data=json.dumps(payload), timeout=self.timeout)
                if response.status_code != 200:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Request failed with status code {response.status_code}"
                    )

                response_data = response.json()
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    content = response_data['choices'][0].get('message', {}).get('content', '')
                    self.last_response = {"text": content}
                    self.conversation.update_chat_history(prompt, content)
                    return {"text": content}
                else:
                    raise exceptions.FailedToGenerateResponseError("No response content found")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
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

    for model in DeepInfra.AVAILABLE_MODELS:
        try:
            test_ai = DeepInfra(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            for chunk in response:
                response_text += chunk
            
            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Clean and truncate response
                clean_text = response_text.strip().encode('utf-8', errors='ignore').decode('utf-8')
                display_text = clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")