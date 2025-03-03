
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
from webscout.Litlogger import Logger, LogFormat, ConsoleHandler
from webscout.Litlogger.core.level import LogLevel

class DeepInfra(Provider):
    """
    A class to interact with the DeepInfra API with logging and LitAgent user-agent.
    """

    AVAILABLE_MODELS = [
        "deepseek-ai/DeepSeek-R1-Turbo",
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "deepseek-ai/DeepSeek-V3",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "mistralai/Mistral-Small-24B-Instruct-2501",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "microsoft/phi-4",
        "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "meta-llama/Meta-Llama-3.1-405B-Instruct",
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "nvidia/Llama-3.1-Nemotron-70B-Instruct",
        "Qwen/Qwen2.5-72B-Instruct",
        "meta-llama/Llama-3.2-90B-Vision-Instruct",
        "meta-llama/Llama-3.2-11B-Vision-Instruct",
        "Gryphe/MythoMax-L2-13b",
        "NousResearch/Hermes-3-Llama-3.1-405B",
        "NovaSky-AI/Sky-T1-32B-Preview",
        "Qwen/Qwen2.5-7B-Instruct",
        "Sao10K/L3.1-70B-Euryale-v2.2",
        "Sao10K/L3.3-70B-Euryale-v2.3",
        "google/gemma-2-27b-it",
        "google/gemma-2-9b-it",
        "meta-llama/Llama-3.2-1B-Instruct",
        "meta-llama/Llama-3.2-3B-Instruct",
        "meta-llama/Meta-Llama-3-70B-Instruct",
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "mistralai/Mistral-Nemo-Instruct-2407",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "mistralai/Mixtral-8x7B-Instruct-v0.1"
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
        model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo",  # Updated default model
        logging: bool = False
    ):
        """Initializes the DeepInfra API client with logging support."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.url = "https://api.deepinfra.com/v1/openai/chat/completions"
        # Use LitAgent for user-agent instead of hardcoded string.
        self.headers = {
            'User-Agent': LitAgent().random(),
            'Accept-Language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://deepinfra.com',
            'Pragma': 'no-cache',
            'Referer': 'https://deepinfra.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'X-Deepinfra-Source': 'web-embed',
            'accept': 'text/event-stream',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
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

        # Initialize logger with proper configuration
        if logging:
            console_handler = ConsoleHandler(
                level=LogLevel.DEBUG,
            )
            
            self.logger = Logger(
                name="DeepInfra",                
                level=LogLevel.DEBUG,
                handlers=[console_handler]
            )
            self.logger.info("DeepInfra initialized successfully ✨")
        else:
            self.logger = None

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        if self.logger:
            self.logger.debug(f"Processing request - Stream: {stream}, Optimizer: {optimizer}")
        
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
                if self.logger:
                    self.logger.info(f"Applied optimizer: {optimizer} 🔧")
            else:
                if self.logger:
                    self.logger.error(f"Invalid optimizer requested: {optimizer}")
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

        if self.logger:
            self.logger.debug(f"Sending request to model: {self.model} 🚀")

        def for_stream():
            if self.logger:
                self.logger.info("Starting stream processing ⚡")
            try:
                with requests.post(self.url, headers=self.headers, data=json.dumps(payload), stream=True, timeout=self.timeout) as response:
                    if response.status_code != 200:
                        if self.logger:
                            self.logger.error(f"Request failed with status {response.status_code} ❌")
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
                                    if self.logger:
                                        self.logger.info("Stream completed successfully ✅")
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
                                    if self.logger:
                                        self.logger.error("Failed to decode JSON response 🔥")
                                    continue
                    
                    self.conversation.update_chat_history(prompt, streaming_text)
                    
            except requests.RequestException as e:
                if self.logger:
                    self.logger.error(f"Request failed: {str(e)} 🔥")
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

        def for_non_stream():
            if self.logger:
                self.logger.debug("Processing non-stream request")
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
    from rich import print
    ai = DeepInfra(timeout=5000, logging=True)
    response = ai.chat("write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
