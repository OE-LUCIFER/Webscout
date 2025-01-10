import cloudscraper
import json
from typing import Any, Dict, Optional

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider
from webscout import exceptions

class RUBIKSAI(Provider):
    """
    A class to interact with the Rubiks.ai API.
    """

    AVAILABLE_MODELS = [
        "gpt-4o-mini", 
        "gemini-1.5-pro"
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
        model: str = "gpt-4o-mini",
        temperature: float = 0.6,
    ) -> None:
        """
        Initializes the RUBIKSAI API with given parameters.

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion.
                                        Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts.
                                            Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): AI model to use. Defaults to "gpt-4o-mini". 
                                    Available models: "gpt-4o-mini", "gemini-1.5-pro"
            temperature (float, optional): Sampling temperature. Defaults to 0.6.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.temperature = temperature
        self.session = cloudscraper.create_scraper()
        self.api_endpoint = "https://rubiks.ai/search/api/"
        
        # Updated headers with all necessary fields
        self.headers = {
            "authority": "rubiks.ai",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://rubiks.ai",
            "referer": f"https://rubiks.ai/search/?q=&model={model}",
            "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
        }

        # Get initial cookies
        init_response = self.session.get("https://rubiks.ai/search/")
        if not init_response.ok:
            raise exceptions.FailedToGenerateResponseError("Failed to initialize session")

        # Extract cf_clearance and other cookies
        self.cookies = {
            'cf_clearance': init_response.cookies.get('cf_clearance', ''),
        }
        
        # Update session with cookies and headers
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies)

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model

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

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        """
        Sends a prompt to the Rubiks.ai API and returns the response.

        Args:
            prompt: The text prompt to generate text from.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            raw (bool, optional): Whether to return the raw response. Defaults to False.
            optimizer (str, optional): The name of the optimizer to use. Defaults to None.
            conversationally (bool, optional): Whether to chat conversationally. Defaults to False.

        Returns:
            The response from the API.
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

        payload = {
            "model": self.model,
            "stream": True,
            "messages": [{"role": "user", "content": conversation_prompt}],
            "temperature": self.temperature,
            "search": ""
        }

        def for_stream():
            try:
                response = self.session.post(
                    self.api_endpoint,
                    json=payload,
                    stream=True,
                    timeout=self.timeout
                )
                
                if response.status_code == 403:
                    # Try to refresh the session
                    init_response = self.session.get("https://rubiks.ai/search/")
                    self.cookies['cf_clearance'] = init_response.cookies.get('cf_clearance', '')
                    self.session.cookies.update(self.cookies)
                    
                    # Retry the request
                    response = self.session.post(
                        self.api_endpoint,
                        json=payload,
                        stream=True,
                        timeout=self.timeout
                    )

                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason})"
                    )

                # ...rest of the streaming code...
                streaming_response = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        if line.startswith("data: "):
                            json_data = line[6:]
                            if json_data == "[DONE]":
                                break
                            try:
                                data = json.loads(json_data)
                                if "choices" in data and len(data["choices"]) > 0:
                                    content = data["choices"][0]["delta"].get("content", "")
                                    streaming_response += content
                                    yield content if raw else dict(text=content)
                            except json.decoder.JSONDecodeError:
                                continue

                self.last_response.update(dict(text=streaming_response))
                self.conversation.update_chat_history(
                    prompt, self.get_message(self.last_response)
                )

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

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
    ai = RUBIKSAI(timeout=5000)
    response = ai.chat("write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)