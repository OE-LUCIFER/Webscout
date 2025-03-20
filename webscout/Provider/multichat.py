import requests
import json
import uuid
from typing import Any, Dict
from datetime import datetime
from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent 

# Model configurations
MODEL_CONFIGS = {
    "llama": {
        "endpoint": "https://www.multichatai.com/api/chat/meta",
        "models": {
            "llama-3.3-70b-versatile": {"contextLength": 131072},
            "llama-3.2-11b-vision-preview": {"contextLength": 32768},
            "deepseek-r1-distill-llama-70b": {"contextLength": 128000},
        },
    },
    "cohere": {
        "endpoint": "https://www.multichatai.com/api/chat/cohere",
        "models": {
            "command-r": {"contextLength": 128000},
            "command": {"contextLength": 4096},
        },
    },
    "google": {
        "endpoint": "https://www.multichatai.com/api/chat/google",
        "models": {
            "gemini-1.5-flash-002": {"contextLength": 1048576},
            "gemma2-9b-it": {"contextLength": 8192},
            "gemini-2.0-flash": {"contextLength": 128000},
                    },
        "message_format": "parts",
    },
    "deepinfra": {
        "endpoint": "https://www.multichatai.com/api/chat/deepinfra",
        "models": {
            "Sao10K/L3.1-70B-Euryale-v2.2": {"contextLength": 8192},
            "Gryphe/MythoMax-L2-13b": {"contextLength": 8192},
            "nvidia/Llama-3.1-Nemotron-70B-Instruct": {"contextLength": 131072},
            "deepseek-ai/DeepSeek-V3": {"contextLength": 32000},
            "meta-llama/Meta-Llama-3.1-405B-Instruct": {"contextLength": 131072},
            "NousResearch/Hermes-3-Llama-3.1-405B": {"contextLength": 131072},
            "gemma-2-27b-it": {"contextLength": 8192},
        },
    },
    "mistral": {
        "endpoint": "https://www.multichatai.com/api/chat/mistral",
        "models": {
            "mistral-small-latest": {"contextLength": 32000},
            "codestral-latest": {"contextLength": 32000},
            "open-mistral-7b": {"contextLength": 8000},
            "open-mixtral-8x7b": {"contextLength": 8000},
        },
    },
    "alibaba": {
        "endpoint": "https://www.multichatai.com/api/chat/alibaba",
        "models": {
            "Qwen/Qwen2.5-72B-Instruct": {"contextLength": 32768},
            "Qwen/Qwen2.5-Coder-32B-Instruct": {"contextLength": 32768},
            "Qwen/QwQ-32B-Preview": {"contextLength": 32768},
        },
    },
}

class MultiChatAI(Provider):
    """
    A class to interact with the MultiChatAI API.
    """
    AVAILABLE_MODELS = [
        # Llama Models
        "llama-3.3-70b-versatile",
        "llama-3.2-11b-vision-preview",
        "deepseek-r1-distill-llama-70b",
        
        # Cohere Models
        # "command-r", >>>> NOT WORKING
        # "command", >>>> NOT WORKING
        
        # Google Models
        # "gemini-1.5-flash-002", >>>> NOT WORKING
        "gemma2-9b-it",
        "gemini-2.0-flash",
        
        # DeepInfra Models
        "Sao10K/L3.1-70B-Euryale-v2.2",
        "Gryphe/MythoMax-L2-13b",
        "nvidia/Llama-3.1-Nemotron-70B-Instruct",
        "deepseek-ai/DeepSeek-V3",
        "meta-llama/Meta-Llama-3.1-405B-Instruct",
        "NousResearch/Hermes-3-Llama-3.1-405B",
        # "gemma-2-27b-it", >>>> NOT WORKING
        
        # Mistral Models
        # "mistral-small-latest", >>>> NOT WORKING
        # "codestral-latest", >>>> NOT WORKING
        # "open-mistral-7b", >>>> NOT WORKING
        # "open-mixtral-8x7b", >>>> NOT WORKING
        
        # Alibaba Models
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "Qwen/QwQ-32B-Preview"
    ]

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
        model: str = "llama-3.3-70b-versatile",
        system_prompt: str = "You are a friendly, helpful AI assistant.",
        temperature: float = 0.5,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1
    ):
        """Initializes the MultiChatAI API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
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
        
        # Initialize LitAgent for user agent generation
        self.agent = LitAgent()
        
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "text/plain;charset=UTF-8",
            "origin": "https://www.multichatai.com",
            "referer": "https://www.multichatai.com/",
            "user-agent": self.agent.random(),
        }
        
        self.session.headers.update(self.headers)
        self.session.proxies = proxies
        self.session.cookies.update({"session": uuid.uuid4().hex})

        self.__available_optimizers = (
            method for method in dir(Optimizers)
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

        self.provider = self._get_provider_from_model(self.model)
        self.model_name = self.model

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

    def _get_system_message(self) -> str:
        """Generate system message with current date."""
        current_date = datetime.now().strftime("%d/%m/%Y")
        return f"Today is {current_date}.\n\nUser Instructions:\n{self.system_prompt}"

    def _build_messages(self, conversation_prompt: str) -> list:
        """Build messages array based on provider type."""
        if self.provider == "google":
            return [
                {"role": "user", "parts": self._get_system_message()},
                {"role": "model", "parts": "I will follow your instructions."},
                {"role": "user", "parts": conversation_prompt}
            ]
        else:
            return [
                {"role": "system", "content": self._get_system_message()},
                {"role": "user", "content": conversation_prompt}
            ]

    def _get_provider_from_model(self, model: str) -> str:
        """Determine the provider based on the model name."""
        for provider, config in MODEL_CONFIGS.items():
            if model in config["models"]:
                return provider
        
        available_models = []
        for provider, config in MODEL_CONFIGS.items():
            for model_name in config["models"].keys():
                available_models.append(f"{provider}/{model_name}")
        
        error_msg = f"Invalid model: {model}\nAvailable models: {', '.join(available_models)}"
        raise ValueError(error_msg)

    def _make_request(self, payload: Dict[str, Any]) -> requests.Response:
        """Make the API request with proper error handling."""
        try:
            response = self.session.post(
                self._get_endpoint(),
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise exceptions.FailedToGenerateResponseError(f"API request failed: {e}") from e

    def ask(
        self,
        prompt: str,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        """Sends a prompt to the MultiChatAI API and returns the response."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                error_msg = f"Optimizer is not one of {self.__available_optimizers}"
                raise exceptions.FailedToGenerateResponseError(error_msg)

        payload = {
            "chatSettings": self._get_chat_settings(),
            "messages": self._build_messages(conversation_prompt),
            "customModelId": "",
        }

        response = self._make_request(payload)
        try:
            full_response = response.text.strip()
            self.last_response = {"text": full_response}
            self.conversation.update_chat_history(prompt, full_response)
            return self.last_response
        except json.JSONDecodeError as e:
            raise exceptions.FailedToGenerateResponseError(f"Invalid JSON response: {e}") from e

    def chat(
        self,
        prompt: str,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """Generate response."""
        response = self.ask(
            prompt, optimizer=optimizer, conversationally=conversationally
        )
        return self.get_message(response)

    def get_message(self, response: Dict[str, Any] | str) -> str:
        """
        Retrieves message from response.
        
        Args:
            response (Union[Dict[str, Any], str]): The response to extract the message from
            
        Returns:
            str: The extracted message text
        """
        if isinstance(response, dict):
            return response.get("text", "")
        return str(response)

if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)
    
    # Test all available models
    working = 0
    total = len(MultiChatAI.AVAILABLE_MODELS)
    
    for model in MultiChatAI.AVAILABLE_MODELS:
        try:
            test_ai = MultiChatAI(model=model, timeout=60)
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