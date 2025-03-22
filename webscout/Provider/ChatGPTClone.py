import time
import uuid
import cloudscraper
import json
import re
from typing import Any, Dict, Optional, Generator, Union
from dataclasses import dataclass, asdict
from datetime import date

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import WEBS, exceptions
from webscout.litagent import LitAgent

class ChatGPTClone(Provider):
    """
    ChatGPTClone is a provider class for interacting with the ChatGPT Clone API.
    Supports streaming responses.
    """
    
    url = "https://chatgpt-clone-ten-nu.vercel.app"
    AVAILABLE_MODELS = ["gpt-4", "gpt-3.5-turbo"]
    
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2000,
        timeout: int = 60,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "gpt-4",
        temperature: float = 0.6,
        top_p: float = 0.7,
        browser: str = "chrome",
        system_prompt: str = "You are a helpful assistant."
    ):
        """Initialize the ChatGPT Clone client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.model = model
        self.session = cloudscraper.create_scraper()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.temperature = temperature
        self.top_p = top_p
        self.system_prompt = system_prompt

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
            "DNT": "1",
            "Origin": self.url,
            "Referer": f"{self.url}/",
            "Sec-CH-UA": self.fingerprint["sec_ch_ua"] or '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self.fingerprint["platform"]}"',
            "User-Agent": self.fingerprint["user_agent"],
        }
        
        # Create session cookies with unique identifiers
        self.cookies = {"__Host-session": uuid.uuid4().hex, '__cf_bm': uuid.uuid4().hex}

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method))
            and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(act, raise_not_found=True, default=None, case_insensitive=True)
            if act
            else intro or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.session.proxies = proxies
        
        # Set consistent headers for the scraper session
        for header, value in self.headers.items():
            self.session.headers[header] = value

    def refresh_identity(self, browser: str = None):
        """Refreshes the browser identity fingerprint."""
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
        
        # Generate new cookies
        self.cookies = {"__Host-session": uuid.uuid4().hex, '__cf_bm': uuid.uuid4().hex}
        
        return self.fingerprint

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        """Send a message to the ChatGPT Clone API"""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ],
            "model": self.model
        }

        def for_stream():
            try:
                with self.session.post(f"{self.url}/api/chat", headers=self.headers, cookies=self.cookies, json=payload, stream=True, timeout=self.timeout) as response:
                    if not response.ok:
                        # If we get a non-200 response, try refreshing our identity once
                        if response.status_code in [403, 429]:
                            self.refresh_identity()
                            # Retry with new identity
                            with self.session.post(f"{self.url}/api/chat", headers=self.headers, cookies=self.cookies, json=payload, stream=True, timeout=self.timeout) as retry_response:
                                if not retry_response.ok:
                                    raise exceptions.FailedToGenerateResponseError(
                                        f"Failed to generate response after identity refresh - ({retry_response.status_code}, {retry_response.reason}) - {retry_response.text}"
                                    )
                                response = retry_response
                        else:
                            raise exceptions.FailedToGenerateResponseError(
                                f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                            )

                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            match = re.search(r'0:"(.*?)"', line)
                            if match:
                                content = match.group(1)
                                streaming_text += content
                                yield content if raw else dict(text=content)
                                
                    self.last_response.update(dict(text=streaming_text))
                    self.conversation.update_chat_history(prompt, streaming_text)
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")

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
    ) -> Union[str, Generator[str, None, None]]:
        """Generate a response to a prompt"""
        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)
                
        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt, False, optimizer=optimizer, conversationally=conversationally
                )
            )
            
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Extract message text from response"""
        assert isinstance(response, dict)
        formatted_text = response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')
        return formatted_text

if __name__ == "__main__":
    from rich import print
    ai = ChatGPTClone(timeout=5000)
    response = ai.chat("write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True) 