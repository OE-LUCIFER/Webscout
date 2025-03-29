import requests
import json
from typing import Union, Any, Dict, Optional, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions


class oivscode(Provider):
    """
    A class to interact with a test API.
    """
    AVAILABLE_MODELS = [
        "deepseek/deepseek-chat",
        "claude-3-5-haiku-20241022",
        "gpt-4o-mini",
        "claude-3-5-sonnet-20240620",
        "ours/deepseek-chat",
        "custom/deepseek",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "claude-3-5-sonnet-20241022",
        "omni-moderation-latest",
        "omni-moderation-latest-intents",
        "omni-moderation-2024-09-26",
        "gpt-4",
        "gpt-4o",
        "gpt-4o-audio-preview",
        "gpt-4o-audio-preview-2024-12-17",
        "gpt-4o-audio-preview-2024-10-01",
        "gpt-4o-mini-audio-preview-2024-12-17",
        "gpt-4o-mini",
        "gpt-4o-mini-2024-07-18",
        "o1",
        "o1-mini",
        "o1-mini-2024-09-12",
        "o1-preview",
        "o1-preview-2024-09-12",
        "o1-2024-12-17",
        "chatgpt-4o-latest",
        "gpt-4o-2024-05-13",
        "gpt-4o-2024-08-06",
        "gpt-4o-2024-11-20",
        "gpt-4o-realtime-preview-2024-10-01",
        "gpt-4o-realtime-preview",
        "gpt-4o-realtime-preview-2024-12-17",
        "gpt-4o-mini-realtime-preview",
        "gpt-4o-mini-realtime-preview-2024-12-17",
        "gpt-4-turbo-preview",
        "gpt-4-0314",
        "gpt-4-0613",
        "gpt-4-32k",
        "gpt-4-32k-0314",
        "gpt-4-32k-0613",
        "gpt-4-turbo",
        "gpt-4-turbo-2024-04-09",
        "gpt-4-1106-preview",
        "gpt-4-0125-preview",
        "gpt-4-vision-preview",
        "gpt-4-1106-vision-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0301",
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-16k-0613",
        "text-embedding-3-large",
        "text-embedding-3-small",
        "text-embedding-ada-002",
        "text-embedding-ada-002-v2",
        "text-moderation-stable",
        "text-moderation-007",
        "text-moderation-latest",
        "256-x-256/dall-e-2",
        "512-x-512/dall-e-2",
        "1024-x-1024/dall-e-2",
        "hd/1024-x-1792/dall-e-3",
        "hd/1792-x-1024/dall-e-3",
        "hd/1024-x-1024/dall-e-3",
        "standard/1024-x-1792/dall-e-3",
        "standard/1792-x-1024/dall-e-3",
        "standard/1024-x-1024/dall-e-3",
        "whisper-1",
        "tts-1",
        "tts-1-hd",
        "ft:davinci-002",
        "ft:babbage-002",
        "babbage-002",
        "davinci-002",
        "gpt-3.5-turbo-instruct",
        "gpt-3.5-turbo-instruct-0914",
        "claude-instant-1",
        "claude-instant-1.2",
        "claude-2",
        "claude-2.1",
        "claude-3-haiku-20240307",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-sonnet-20241022",
        "togethercomputer/llama-2-70b-chat",
        "togethercomputer/llama-2-70b",
        "togethercomputer/LLaMA-2-7B-32K",
        "togethercomputer/Llama-2-7B-32K-Instruct",
        "togethercomputer/llama-2-7b",
        "togethercomputer/falcon-40b-instruct",
        "togethercomputer/falcon-7b-instruct",
        "togethercomputer/alpaca-7b",
        "HuggingFaceH4/starchat-alpha",
        "togethercomputer/CodeLlama-34b",
        "togethercomputer/CodeLlama-34b-Instruct",
        "togethercomputer/CodeLlama-34b-Python",
        "defog/sqlcoder",
        "NumbersStation/nsql-llama-2-7B",
        "WizardLM/WizardCoder-15B-V1.0",
        "WizardLM/WizardCoder-Python-34B-V1.0",
        "NousResearch/Nous-Hermes-Llama2-13b",
        "Austism/chronos-hermes-13b",
        "upstage/SOLAR-0-70b-16bit",
        "WizardLM/WizardLM-70B-V1.0",
        "deepseek/deepseek-chat",
        "deepseek/deepseek-coder",
        "fireworks_ai/accounts/fireworks/models/llama-v3p2-1b-instruct",
        "fireworks_ai/accounts/fireworks/models/llama-v3p2-3b-instruct",
        "fireworks_ai/accounts/fireworks/models/llama-v3p2-11b-vision-instruct",
        "accounts/fireworks/models/llama-v3p2-90b-vision-instruct",
        "fireworks_ai/accounts/fireworks/models/firefunction-v2",
        "fireworks_ai/accounts/fireworks/models/mixtral-8x22b-instruct-hf",
        "fireworks_ai/accounts/fireworks/models/qwen2-72b-instruct",
        "fireworks_ai/accounts/fireworks/models/qwen2p5-coder-32b-instruct",
        "fireworks_ai/accounts/fireworks/models/yi-large",
        "fireworks_ai/accounts/fireworks/models/deepseek-coder-v2-instruct",
        "fireworks_ai/accounts/fireworks/models/deepseek-v3",
        "fireworks_ai/nomic-ai/nomic-embed-text-v1.5",
        "fireworks_ai/nomic-ai/nomic-embed-text-v1",
        "fireworks_ai/WhereIsAI/UAE-Large-V1",
        "fireworks_ai/thenlper/gte-large",
        "fireworks_ai/thenlper/gte-base",
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 1024,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "claude-3-5-sonnet-20240620",
        system_prompt: str = "You are a helpful AI assistant.",
        
    ):
        """
        Initializes the oivscode with given parameters.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")


        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://oi-vscode-server.onrender.com/v1/chat/completions"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,en-GB;q=0.8,en-IN;q=0.7",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site"
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
    ) -> Union[Dict[str, Any], Generator[Any, None, None]][Dict[str, Any], None, None]:
        """Chat with AI

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            dict or generator: 
                If stream is False, returns a dict
                If stream is True, returns a generator
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
            "stream": stream,
             "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ]
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            message_load = ""
            for value in response.iter_lines(
                decode_unicode=True,
                delimiter="" if raw else "data:",
                chunk_size=64,
            ):
                try:
                    resp = json.loads(value)
                    incomplete_message = self.get_message(resp)
                    if incomplete_message:
                        message_load += incomplete_message
                        resp["choices"][0]["delta"]["content"] = message_load
                        self.last_response.update(resp)
                        yield value if raw else resp
                    elif raw:
                        yield value
                except json.decoder.JSONDecodeError:
                    pass
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=False, timeout=self.timeout
            )
            if (
                not response.ok
                or not response.headers.get("Content-Type", "") == "application/json"
            ):
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )
            resp = response.json()
            self.last_response.update(resp)
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            return resp

        return for_stream() if stream else for_non_stream()


    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
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
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    chatbot = oivscode()
    response = chatbot.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)