import requests
import json
import re
from typing import Union, Any, Dict, Optional, Generator

from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent

class JadveOpenAI(Provider):
    """
    A class to interact with the OpenAI API through jadve.com using the streaming endpoint.
    """

    AVAILABLE_MODELS = ["gpt-4o", "gpt-4o-mini", "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20240620", "o1-mini", "deepseek-chat", "o1-mini", "claude-3-5-haiku-20241022"]

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
        model: str = "claude-3-7-sonnet-20250219",
        system_prompt: str = "You are a helpful AI assistant."
    ):
        """
        Initializes the JadveOpenAI client.

        Args:
            is_conversation (bool, optional): Enable conversational mode. Defaults to True.
            max_tokens (int, optional): Maximum tokens for generation. Defaults to 600.
            timeout (int, optional): HTTP request timeout in seconds. Defaults to 30.
            intro (str, optional): Introductory prompt text. Defaults to None.
            filepath (str, optional): Path to conversation history file. Defaults to None.
            update_file (bool, optional): Whether to update the conversation history file. Defaults to True.
            proxies (dict, optional): Proxies for HTTP requests. Defaults to {}.
            history_offset (int, optional): Limit for conversation history. Defaults to 10250.
            act (str|int, optional): Act key for AwesomePrompts. Defaults to None.
            model (str, optional): AI model to be used. Defaults to "gpt-4o-mini".
            system_prompt (str, optional): System prompt text. Defaults to "You are a helpful AI assistant."
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://openai.jadve.com/stream"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt

        # Headers for API requests
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://jadve.com",
            "priority": "u=1, i",
            "referer": "https://jadve.com/",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": LitAgent().random(),
            "x-authorization": "Bearer"
        }
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

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

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[dict, Generator[dict, None, None]]:
        """
        Chat with AI.

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Return raw content chunks. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Flag for conversational optimization. Defaults to False.
        Returns:
            dict or generator: A dictionary with the generated text or a generator yielding text chunks.
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {list(self.__available_optimizers)}"
                )

        payload = {
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": conversation_prompt}]}
            ],
            "model": self.model,
            "botId": "",
            "chatId": "",
            "stream": stream,
            "temperature": 0.7,
            "returnTokensUsage": True,
            "useTools": False
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint, headers=self.headers, json=payload, stream=True, timeout=self.timeout
            )

            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            # Pattern to match the streaming chunks format: 0:"text"
            pattern = r'0:"(.*?)"'
            full_response_text = ""
            
            # Process the response as it comes in
            buffer = ""
            
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                
                buffer += line
                
                # Try to match chunks in the current buffer
                matches = re.findall(pattern, buffer)
                if matches:
                    for chunk in matches:
                        full_response_text += chunk
                        # Return the current chunk
                        yield chunk if raw else dict(text=chunk)
                    
                    # Remove matched parts from the buffer
                    matched_parts = [f'0:"{match}"' for match in matches]
                    for part in matched_parts:
                        buffer = buffer.replace(part, '', 1)
                
                # Check if we've reached the end of the response
                if 'e:' in line or 'd:' in line:
                    # No need to process usage data without logging
                    break

            self.last_response.update(dict(text=full_response_text))
            self.conversation.update_chat_history(prompt, self.get_message(self.last_response))

        def for_non_stream():
            # For non-streaming requests, we collect all chunks and return the complete response
            collected_text = ""
            for chunk in for_stream():
                if raw:
                    collected_text += chunk
                else:
                    collected_text += chunk.get("text", "")
            
            self.last_response = {"text": collected_text}
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Generate a chat response (string).

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name. Defaults to None.
            conversationally (bool, optional): Flag for conversational optimization. Defaults to False.
        Returns:
            str or generator: Generated response string or generator yielding response chunks.
        """
        def for_stream():
            for response in self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(prompt, stream=False, optimizer=optimizer, conversationally=conversationally)
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """
        Retrieves message from the response.

        Args:
            response (dict): Response from the ask() method.
        Returns:
            str: Extracted text.
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)

    for model in JadveOpenAI.AVAILABLE_MODELS:
        try:
            test_ai = JadveOpenAI(model=model, timeout=60)
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