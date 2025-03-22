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

class LabyrinthAI(Provider):
    """
    A class to interact with the Labyrinth AI chat API.
    """

    # AVAILABLE_MODELS = [
    #     "gemini-2.0-flash"
    # ]

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
        # model: str = "gemini-2.0-flash",
        browser: str = "chrome"
    ):
        """Initializes the Labyrinth AI API client."""
        # if model not in self.AVAILABLE_MODELS:
        #     raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.url = "https://labyrinth-ebon.vercel.app/api/chat"
        
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
            "Origin": "https://labyrinth-ebon.vercel.app",
            "Cookie": "stock-mode=false; __Host-next-auth.csrf-token=68aa6224f2ff7bbf2c4480a90c49b7b95aaac01a63ed90f3d20a69292c16a366%7C1f6672653c6e304ea971373fecdc3fe491568d014c68cdf3b26ead42f1c6ac62; __Secure-next-auth.callback-url=https%3A%2F%2Flabyrinth-ebon.vercel.app%2F; selectedModel={\"id\":\"gemini-2.0-flash\",\"name\":\"Gemini 2.0 Flash\",\"provider\":\"Google Generative AI\",\"providerId\":\"google\",\"enabled\":true,\"toolCallType\":\"native\",\"searchMode\":true}; __Secure-next-auth.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..Z5-1j_rsCWRHY17B.s0lMkhWr0S7a3-4h2p-ce0NJHeNyh8nDyOcsrzFU8AZtBbygGcHKbJ8PzLLQBNL7NwrUwET3fKGbtnAphaVjuSJQfXA0tu69zKJELPw-A3x0Ev6aHJMTG3l9_SweByHyfCSCnGB7tvjwEFsW4c5xs_HzMdPmoRTYyYzlZPuDGhHtQX7WyeUiARc36NfwV-KJYpzXV5-g0VkpsxFEawcfdk6D_S7JtOMmjMTTYuw2BbNYvtlvM-n_XivIctQmQ5Fp65JEE73nr5hWVReyYrkyfUGt4Q.TP8Woa-7Ao05yVCjbbGDug",
            "Referer": "https://labyrinth-ebon.vercel.app/",
            "Sec-CH-UA": self.fingerprint["sec_ch_ua"] or '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self.fingerprint["platform"]}"',
            "User-Agent": self.fingerprint["user_agent"],
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1"
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        # self.model = model

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

        # Prepare the request payload
        payload = {
            "id": str(uuid.uuid4()),
            "messages": [
                {
                    "role": "user",
                    "content": conversation_prompt,
                    "parts": [{"type": "text", "text": conversation_prompt}]
                }
            ],
            "stockMode": False
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
                                if line.startswith('0:'):
                                    content = line[2:].strip('"')
                                    streaming_text += content
                                    resp = dict(text=content)
                                    yield resp if raw else resp
                            except UnicodeDecodeError:
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
                            if line.startswith('0:'):
                                content = line[2:].strip('"')
                                full_response += content
                        except UnicodeDecodeError:
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
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')
