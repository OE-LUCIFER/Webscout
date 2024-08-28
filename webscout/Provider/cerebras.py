import json
import requests
from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from typing import Dict, Any

class Cerebras(Provider):
    """
    A class to interact with the Cerebras AI API.
    """

    AVAILABLE_MODELS = ["llama3.1-8b", "llama3.1-70b"]

    def __init__(
        self,
        api_key: str,
        is_conversation: bool = True,
        max_tokens: int = 4096,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "llama3.1-8b",
        system_prompt: str = "Please try to provide useful, helpful and actionable answers.",
    ):
        """
        Initializes the Cerebras AI API with given parameters.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Available models are: {', '.join(self.AVAILABLE_MODELS)}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://api.cerebras.ai/v1/chat/completions"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "authorization": f"Bearer {api_key}",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://inference.cerebras.ai",
            "referer": "https://inference.cerebras.ai/",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
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

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
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
                {"role": "user", "content": conversation_prompt},
            ],
            "model": self.model,
            "stream": True,
            "temperature": 0.2,
            "top_p": 1,
            "max_tokens": self.max_tokens_to_sample
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint, json=payload, stream=True, timeout=self.timeout
            )

            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason})"
                )

            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_data = line.decode('utf-8').strip()
                    if line_data.startswith("data: "):
                        json_str = line_data[6:]
                        if json_str != "[DONE]":
                            chunk = json.loads(json_str)
                            if 'choices' in chunk and 'delta' in chunk['choices'][0]:
                                content = chunk['choices'][0]['delta'].get('content', '')
                                full_response += content
                                yield content if raw else dict(text=content)
                        else:
                            break

            self.last_response.update(dict(text=full_response))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            full_response = ""
            for chunk in for_stream():
                if isinstance(chunk, dict):
                    full_response += chunk['text']
                else:
                    full_response += chunk
            return dict(text=full_response)

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
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
    
    # You can replace this with your actual API key
    api_key = "YOUR_API_KEY_HERE"
    
    ai = Cerebras(api_key=api_key)
    response = ai.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
