from typing import Any, Dict
import requests
import json

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions

class DiscordRocks(Provider):
    """
    A class to interact with the Airforce API.
    """

    AVAILABLE_MODELS = [
        'claude-3-haiku-20240307', 'claude-3-sonnet-20240229', 'claude-3-5-sonnet-20240620',
        'claude-3-opus-20240229', 'chatgpt-4o-latest', 'gpt-4', 'gpt-4-0613', 'gpt-4-turbo',
        'gpt-4o-mini-2024-07-18', 'gpt-4o-mini', 'gpt-3.5-turbo', 'gpt-3.5-turbo-0125',
        'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k-0613',
        'gpt-4o', 'llama-3-70b-chat', 'llama-3-70b-chat-turbo', 'llama-3-8b-chat',
        'llama-3-8b-chat-turbo', 'llama-3-70b-chat-lite', 'llama-3-8b-chat-lite',
        'llama-2-13b-chat', 'llama-3.1-405b-turbo', 'llama-3.1-70b-turbo', 'llama-3.1-8b-turbo',
        'LlamaGuard-2-8b', 'Llama-Guard-7b', 'Meta-Llama-Guard-3-8B', 'Mixtral-8x7B-v0.1',
        'Mixtral-8x7B-Instruct-v0.1', 'Mixtral-8x22B-Instruct-v0.1', 'Mistral-7B-Instruct-v0.1',
        'Mistral-7B-Instruct-v0.2', 'Mistral-7B-Instruct-v0.3', 'Qwen1.5-72B-Chat',
        'Qwen1.5-110B-Chat', 'Qwen2-72B-Instruct', 'gemma-2b-it', 'dbrx-instruct',
        'deepseek-coder-33b-instruct', 'deepseek-llm-67b-chat', 'Nous-Hermes-2-Mixtral-8x7B-DPO',
        'Nous-Hermes-2-Yi-34B', 'WizardLM-2-8x22B', 'CodeLlama-7b-Python',
        'snowflake-arctic-instruct', 'SOLAR-10.7B-Instruct-v1.0', 'StripedHyena-Nous-7B',
        'CodeLlama-13b-Instruct', 'MythoMax-L2-13b', 'gemma-2-9b-it', 'gemma-2-27b-it',
        'gemini-1.5-flash', 'gemini-1.5-pro', 'sparkdesk', 'cosmosrp'
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
        system_prompt: str = "You are a helpful AI assistant.",
        model: str = "chatgpt-4o-latest",
        temperature: float = 1,
        top_p: float = 1,
    ):
        """
        Initializes the Airforce API with given parameters.

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
            system_prompt (str, optional): System prompt for Airforce. Defaults to "You are a helpful AI assistant.".
            model (str, optional): AI model to use. Defaults to "chatgpt-4o-latest". 
            temperature (float, optional): Temperature parameter for the model. Defaults to 1.
            top_p (float, optional): Top_p parameter for the model. Defaults to 1.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f'Error: Invalid model. Please choose from {self.AVAILABLE_MODELS}')

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://api.airforce/chat/completions"
        self.stream_chunk_size = 1024
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'authorization': 'Bearer missing api key',
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://llmplayground.net',
            'referer': 'https://llmplayground.net/',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'
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
        """Chat with AI"""
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
            'messages': [{'role': 'user', 'content': conversation_prompt}],
            'model': self.model,
            'max_tokens': self.max_tokens_to_sample,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'stream': stream
        }

        def for_stream():
            try:
                # Send the POST request
                response = self.session.post(self.api_endpoint, headers=self.headers, json=payload, stream=True)
                
                # Check if the request was successful
                response.raise_for_status()
                
                full_content = ''
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            if decoded_line.strip() == 'data: [DONE]':
                                break
                            try:
                                json_data = json.loads(decoded_line[5:])
                                content = json_data['choices'][0]['delta'].get('content', '')
                                if content:
                                    full_content += content
                                    yield content if raw else dict(text=content)
                            except json.JSONDecodeError:
                                print(f'Error decoding JSON: {decoded_line}')
                            except KeyError:
                                print(f'Unexpected JSON structure: {json_data}')
                self.last_response.update(dict(text=full_content))
                self.conversation.update_chat_history(
                    prompt, self.get_message(self.last_response)
                )
            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f'An error occurred: {e}')

        def for_non_stream():
            try:
                # Send the POST request
                response = self.session.post(self.api_endpoint, headers=self.headers, json=payload)
                
                # Check if the request was successful
                response.raise_for_status()
                
                resp = response.json()
                self.last_response.update(dict(text=resp.get("choices", [{}])[0].get('message', {}).get('content', '')))
                self.conversation.update_chat_history(
                    prompt, self.get_message(self.last_response)
                )
                return self.last_response
            except requests.exceptions.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f'An error occurred: {e}')

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
    ai = DiscordRocks(timeout=5000)
    response = ai.chat("write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
