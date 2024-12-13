import requests
import json
from typing import Any, Dict, Optional, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions

# Model configurations
MODEL_CONFIGS = {
    "llama": {
        "endpoint": "https://www.multichatai.com/api/chat/meta",
        "models": {
            "llama-3.1-70b-versatile": {"contextLength": 8192},
            "llama-3.2-90b-vision-preview": {"contextLength": 32768},
            "llama-3.2-11b-vision-preview": {"contextLength": 32768},
        },
    },
    "alibaba": {
        "endpoint": "https://www.multichatai.com/api/chat/alibaba",
        "models": {
            "Qwen/Qwen2.5-72B-Instruct": {"contextLength": 32768},
            "Qwen/Qwen2.5-Coder-32B-Instruct": {"contextLength": 32768},
        },
    },
    "cohere": {
        "endpoint": "https://www.multichatai.com/api/chat/cohere",
        "models": {"command-r": {"contextLength": 128000}},
    },
}

class MultiChatAI(Provider):
    """
    A class to interact with the MultiChatAI API.
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 4000,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "llama-3.1-70b-versatile",  # Default model
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.5,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1,
    ):
        """Initializes the MultiChatAI API client."""
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "text/plain;charset=UTF-8",
            "origin": "https://www.multichatai.com",
            "referer": "https://www.multichatai.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

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

        # Parse provider and model name
        self.provider = "llama"  # Default provider
        self.model_name = self.model
        
        # Check if model exists in any provider
        model_found = False
        for provider, config in MODEL_CONFIGS.items():
            if self.model in config["models"]:
                self.provider = provider
                self.model_name = self.model
                model_found = True
                break
        
        if not model_found:
            available_models = []
            for provider, config in MODEL_CONFIGS.items():
                for model in config["models"].keys():
                    available_models.append(f"{provider}/{model}")
            raise ValueError(
                f"Invalid model: {self.model}\nAvailable models: {', '.join(available_models)}"
            )

    def _get_endpoint(self) -> str:
        """Get the API endpoint for the current provider."""
        return MODEL_CONFIGS[self.provider]["endpoint"]

    def _get_chat_settings(self) -> Dict[str, Any]:
        """Get chat settings for the current model."""
        base_settings = MODEL_CONFIGS[self.provider]["models"][self.model_name]
        return {
            "model": self.model,
            "prompt": self.system_prompt,
            "temperature": self.temperature,
            "contextLength": base_settings["contextLength"],
            "includeProfileContext": True,
            "includeWorkspaceInstructions": True,
            "embeddingsProvider": "openai"
        }

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator:
        """Sends a prompt to the MultiChatAI API and returns the response."""
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

        payload = {
            "chatSettings": self._get_chat_settings(),
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "customModelId": "",
        }

        try:
            response = self.session.post(
                self._get_endpoint(),
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=self.timeout,
            )
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    if stream:
                        yield {"text": decoded_line}
                    full_response += decoded_line

            self.last_response = {"text": full_response.strip()}
            self.conversation.update_chat_history(prompt, full_response.strip())
            
            if not stream:
                return self.last_response

        except requests.exceptions.RequestException as e:
            raise exceptions.ProviderConnectionError(f"API request failed: {e}") from e
        except json.JSONDecodeError as e:
            raise exceptions.InvalidResponseError(f"Invalid JSON response: {e}") from e
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Unexpected error: {e}") from e

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:
        """Generate response."""
        if stream:
            for chunk in self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            ):
                if isinstance(chunk, dict):
                    yield chunk.get("text", "")
                else:
                    yield str(chunk)
        else:
            response = self.ask(
                prompt, stream=False, optimizer=optimizer, conversationally=conversationally
            )
            return response.get("text", "") if isinstance(response, dict) else str(response)

    def get_message(self, response: Dict[str, Any] | str) -> str:
        """Retrieves message from response."""
        if isinstance(response, dict):
            return response.get("text", "")
        return str(response)

if __name__ == "__main__":
    from rich import print

    ai = MultiChatAI(model="llama-3.1-70b-versatile")
    response = ai.chat("What is the meaning of life?", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)