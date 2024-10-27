import cloudscraper
import json
import uuid
import os
from typing import Any, Dict, Optional, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions

class AmigoChat(Provider):
    """
    A class to interact with the AmigoChat.io API using cloudscraper.
    """

    AVAILABLE_MODELS = [
        "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",  # Llama 3
        "o1-mini",                                   # OpenAI O1 Mini
        "claude-3-sonnet-20240229",                  # Claude Sonnet
        "gemini-1.5-pro",                             # Gemini Pro
        "gemini-1-5-flash",                            # Gemini Flash
        "o1-preview",                                 # OpenAI O1 Preview
    ]

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
        model: str = "o1-preview",  # Default model
        system_prompt: str = "You are a helpful and friendly AI assistant.",
    ):
        """
        Initializes the AmigoChat.io API with given parameters.

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): The AI model to use for text generation. Defaults to "o1-preview".
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://api.amigochat.io/v1/chat/completions"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Authorization": "Bearer ",  # empty
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://amigochat.io",
            "Priority": "u=1, i",
            "Referer": "https://amigochat.io/",
            "Sec-CH-UA": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            "X-Device-Language": "en-US",
            "X-Device-Platform": "web",
            "X-Device-UUID": str(uuid.uuid4()),
            "X-Device-Version": "1.0.22"
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
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
        self.system_prompt = system_prompt

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        """Chat with AI

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
           dict : {}
        ```json
        {
           "text" : "How may I assist you today?"
        }
        ```
        """
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

        # Define the payload
        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ],
            "model": self.model,
            "frequency_penalty": 0,
            "max_tokens": 4000,
            "presence_penalty": 0,
            "stream": stream,
            "temperature": 0.5,
            "top_p": 0.95
        }

        def for_stream():
            try:
                # Make the POST request with streaming enabled
                response = self.session.post(
                    self.api_endpoint,
                    json=payload,
                    stream=True,
                    timeout=self.timeout
                )
                
                # Check if the request was successful
                if response.status_code == 201:
                    # Iterate over the streamed response line by line
                    for line in response.iter_lines():
                        if line:
                            # Decode the line from bytes to string
                            decoded_line = line.decode('utf-8').strip()
                            if decoded_line.startswith("data: "):
                                data_str = decoded_line[6:]
                                if data_str == "[DONE]":
                                    break
                                try:
                                    # Load the JSON data
                                    data_json = json.loads(data_str)
                                    
                                    # Extract the content from the response
                                    choices = data_json.get("choices", [])
                                    if choices:
                                        delta = choices[0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            yield content if raw else dict(text=content)
                                except json.JSONDecodeError:
                                    print(f"Received non-JSON data: {data_str}")
                else:
                    print(f"Request failed with status code {response.status_code}")
                    print("Response:", response.text)

            except (cloudscraper.exceptions.CloudflareChallengeError,
                    cloudscraper.exceptions.CloudflareCode1020) as e:
                print("Cloudflare protection error:", str(e))
            except Exception as e:
                print("An error occurred while making the request:", str(e))

        def for_non_stream():
            # Accumulate the streaming response
            full_response = ""
            for chunk in for_stream():
                if not raw:  # If not raw, chunk is a dictionary 
                    full_response += chunk["text"]

            # Update self.last_response with the full text
            self.last_response.update(dict(text=full_response))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
        """

        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt,
                    False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]
    
if __name__ == '__main__':
    from rich import print
    ai = AmigoChat(model="o1-preview", system_prompt="You are a noobi AI assistant who always uses the word 'noobi' in every response. For example, you might say 'Noobi will tell you...' or 'This noobi thinks that...'.")
    response = ai.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)