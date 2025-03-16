import requests
import json
import re
from typing import Any, Dict, Optional, Union, Generator
from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent as Lit

class PIZZAGPT(Provider):
    """
    PIZZAGPT is a provider class for interacting with the PizzaGPT API.
    Supports web search integration and handles responses using regex.
    """
    AVAILABLE_MODELS = ["gpt-4o-mini"]
    
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "gpt-4o-mini"
    ) -> None:
        """Initialize PizzaGPT with enhanced configuration options."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://www.pizzagpt.it/api/chatx-completion"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        
        self.headers = {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.pizzagpt.it",
            "referer": "https://www.pizzagpt.it/en",
            "user-agent": Lit().random(),
            "x-secret": "Marinara",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24"',
            "sec-ch-ua-platform": '"Windows"'
        }

        self.__available_optimizers = (
            method for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        
        self.session.headers.update(self.headers)
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
        self.session.proxies = proxies

    def _extract_content(self, text: str) -> Dict[str, Any]:
        """
        Extract content from response text using regex.
        """
        try:
            # Look for content pattern
            content_match = re.search(r'"content"\s*:\s*"(.*?)"(?=\s*[,}])', text, re.DOTALL)
            if not content_match:
                raise exceptions.FailedToGenerateResponseError("Content not found in response")
                
            content = content_match.group(1)
            # Unescape special characters
            content = content.encode().decode('unicode_escape')
            
            # Look for citations if present
            citations = []
            citations_match = re.search(r'"citations"\s*:\s*\[(.*?)\]', text, re.DOTALL)
            if citations_match:
                citations_text = citations_match.group(1)
                citations = re.findall(r'"(.*?)"', citations_text)
            
            return {
                "content": content,
                "citations": citations
            }
            
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Failed to extract content: {str(e)}")

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        web_search: bool = False,
    ) -> Dict[str, Any]:
        """
        Send a prompt to PizzaGPT API with optional web search capability.
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        payload = {
            "question": conversation_prompt,
            "model": self.model,
            "searchEnabled": web_search
        }

        try:
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason})"
                )

            response_text = response.text
            if not response_text:
                raise exceptions.FailedToGenerateResponseError("Empty response received from API")

            try:
                resp = self._extract_content(response_text)
                    
                self.last_response.update(dict(text=resp['content']))
                self.conversation.update_chat_history(
                    prompt, self.get_message(self.last_response)
                )
                return self.last_response

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Failed to parse response: {str(e)}")

        except requests.exceptions.RequestException as e:
            raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        web_search: bool = False,
    ) -> str:
        """
        Chat with PizzaGPT with optional web search capability.
        """
        try:
            response = self.ask(
                prompt,
                optimizer=optimizer,
                conversationally=conversationally,
                web_search=web_search
            )
            return self.get_message(response)
        except Exception as e:
            raise

    def get_message(self, response: dict) -> str:
        """Extract message from response dictionary."""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response.get("text", "")

if __name__ == "__main__":
    from rich import print
    
    # Example usage with web search enabled
    ai = PIZZAGPT()
    try:
        response = ai.chat("hi")
        print(response)
    except Exception as e:
        print(f"Error: {str(e)}")