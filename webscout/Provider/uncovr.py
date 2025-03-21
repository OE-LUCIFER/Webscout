import requests
import json
import uuid
from typing import Any, Dict, Optional, Generator, Union
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent

class UncovrAI(Provider):
    """
    A class to interact with the Uncovr AI chat API.
    """

    AVAILABLE_MODELS = [
        "default",
        "gpt-4o-mini",
        "gemini-2-flash",
        "o3-mini",
        "claude-3-7-sonnet",
        "gpt-4o",
        "claude-3-5-sonnet-v2",
        "groq-llama-3-1-8b",
        "deepseek-r1-distill-llama-70b",
        "deepseek-r1-distill-qwen-32b",
        "gemini-2-flash-lite-preview",
        "qwen-qwq-32b"
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
        model: str = "default",
        chat_id: str = None,
        user_id: str = None,
        browser: str = "chrome"
    ):
        """Initializes the Uncovr AI API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.url = "https://uncovr.app/api/workflows/chat"
        
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
            "Origin": "https://uncovr.app",
            "Referer": "https://uncovr.app/",
            "Sec-CH-UA": self.fingerprint["sec_ch_ua"] or '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self.fingerprint["platform"]}"',
            "User-Agent": self.fingerprint["user_agent"],
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.chat_id = chat_id or str(uuid.uuid4())
        self.user_id = user_id or f"user_{str(uuid.uuid4())[:8].upper()}"

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
        temperature: int = 32,
        creativity: str = "medium",
        selected_focus: list = ["web"],
        selected_tools: list = ["quick-cards"]
    ) -> Union[Dict[str, Any], Generator]:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        # Prepare the request payload
        payload = {
            "content": conversation_prompt,
            "chatId": self.chat_id,
            "userMessageId": str(uuid.uuid4()),
            "ai_config": {
                "selectedFocus": selected_focus,
                "selectedTools": selected_tools,
                "agentId": "chat",
                "modelId": self.model,
                "temperature": temperature,
                "creativity": creativity
            }
        }

        def for_stream():
            try:
                with self.session.post(self.url, json=payload, stream=True, timeout=self.timeout) as response:
                    if response.status_code != 200:
                        # If we get a non-200 response, try refreshing our identity once
                        if response.status_code in [403, 429]:
                            self.refresh_identity()
                            # Retry with new identity
                            with self.session.post(self.url, json=payload, stream=True, timeout=self.timeout) as retry_response:
                                if not retry_response.ok:
                                    raise exceptions.FailedToGenerateResponseError(
                                        f"Failed to generate response after identity refresh - ({retry_response.status_code}, {retry_response.reason}) - {retry_response.text}"
                                    )
                                response = retry_response
                        else:
                            raise exceptions.FailedToGenerateResponseError(
                                f"Request failed with status code {response.status_code}"
                            )
                    
                    streaming_text = ""
                    for line in response.iter_lines():
                        if line:
                            try:
                                line = line.decode('utf-8')
                                # Handle different message types
                                if line.startswith('0:'):  # Content message
                                    content = line[2:].strip('"')
                                    streaming_text += content
                                    resp = dict(text=content)
                                    yield resp if raw else resp
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                continue
                    
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)
                    
            except requests.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

        def for_non_stream():
            try:
                response = self.session.post(self.url, json=payload, timeout=self.timeout)
                if response.status_code != 200:
                    if response.status_code in [403, 429]:
                        self.refresh_identity()
                        response = self.session.post(self.url, json=payload, timeout=self.timeout)
                        if not response.ok:
                            raise exceptions.FailedToGenerateResponseError(
                                f"Failed to generate response after identity refresh - ({response.status_code}, {response.reason}) - {response.text}"
                            )
                    else:
                        raise exceptions.FailedToGenerateResponseError(
                            f"Request failed with status code {response.status_code}"
                        )

                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            line = line.decode('utf-8')
                            if line.startswith('0:'):  # Content message
                                content = line[2:].strip('"')
                                full_response += content
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue

                self.last_response = {"text": full_response}
                self.conversation.update_chat_history(prompt, full_response)
                return {"text": full_response}
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {e}")

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        temperature: int = 32,
        creativity: str = "medium",
        selected_focus: list = ["web"],
        selected_tools: list = []
    ) -> Union[str, Generator[str, None, None]]:
        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally,
                temperature=temperature, creativity=creativity,
                selected_focus=selected_focus, selected_tools=selected_tools
            ):
                yield self.get_message(response)
        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt, False, optimizer=optimizer, conversationally=conversationally,
                    temperature=temperature, creativity=creativity,
                    selected_focus=selected_focus, selected_tools=selected_tools
                )
            )
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')

if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in UncovrAI.AVAILABLE_MODELS:
        try:
            test_ai = UncovrAI(model=model, timeout=60)
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

