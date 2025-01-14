import uuid
from typing import Any, Dict
import requests
import json

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent


class Qwenlm(Provider):
    """
    A class to interact with the Qwenlm API.
    """

    AVAILABLE_MODELS = [
        'qwen2.5-coder-32b-instruct', 'qwen-plus-latest', 'qvq-72b-preview',
        'qvq-32b-preview', 'qwen-vl-max-latest'
    ]

    def __init__(
            self,
            is_conversation: bool = True,
            max_tokens: int = 1000,
            timeout: int = 30,
            intro: str = None,
            filepath: str = None,
            update_file: bool = True,
            proxies: dict = {},
            history_offset: int = 10250,
            act: str = None,
            system_prompt: str = "You are a helpful AI assistant.",
            model: str = "qwen-plus-latest",
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
        self.api_endpoint = "https://chat.qwenlm.ai/api/chat/completions"
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
            'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImFkNjUxMDc1LTQxNjAtNDY0YS1iMzMyLTQwNWYwNmQ1NDMyNCIsImV4cCI6MTczOTM2NjY5OH0.2lVKlKzc--eXHUmQnjRBaiBNFmJL62vHksDFR79Y_-o',
            'content-type': 'application/json',
            'cookie': 'acw_tc=8448e7002b000a494727db5f2801a32669762f49b770eb56db8ef887a0a4c705; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImFkNjUxMDc1LTQxNjAtNDY0YS1iMzMyLTQwNWYwNmQ1NDMyNCIsImV4cCI6MTczOTM2NjcyMH0.wsZ_GgNDv1igVexh1Pyg17pgSMcV973tkIaGAdwtrwY; SERVERID=b7ad2431ebf120e1ae9c6d3d77d4b099|1736774742|1736774655; SERVERCORSID=b7ad2431ebf120e1ae9c6d3d77d4b099|1736774742|1736774655; isg=BMjIvGMxO26qm1fqP00-15swmTbacSx7vghNnoJ5EMM2XWDHBYPmCQwb0ast9uRT; tfstk=gkOj7Xf7EoqbTSiMEn0PAjqEoECsc4lUkP_9-FF4WsCAfPtwJOQ4gqvs53SroE5xm3aR5H7TDVDGyQ_Dv-I9kGLRyHsSSNHGHQTR-NugkA0gyaQpvlK6SqbOXhK1bKkrTEYcs1necXleoMSEvRxfkiU-Ww7b64WY6Khqs1nEYbJhK8kG6nJ5fPAWygb1WZFvX_eRJgQT6OKO2TQd8oC9X135wN7T6SFAD7LRWgIO6OFtPUIl51Qxw6zdyRs9lqMkMCOascYVV5F9NaQ5iEsfrwA5oT6EtgVOzQ_fhMLXgB96GadyN9Wz705J-L-AP6GzH6LWBH9pjvylGFpvjTtmq8syeL8OX9aQO1B1cLdAFPF9ysSOddtjc-jv336hyTUsta-F2EAvFVqJkHSfMaBr92TRBLRcKIo8G6pHusJ9jvylGFpANg78TMTwsRwGD5_5Y4g7IRmYbFdHfRDq3tQlrY0SPJicHab5A4g7IJBAraDoP4wIm',
            'dnt': '1',
            'origin': 'https://chat.qwenlm.ai',
            'referer': 'https://chat.qwenlm.ai/c/82f27fb4-8d50-404f-b2b1-042b9bf847d8',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': LitAgent().random()
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
            'chat_id': str(uuid.uuid4()),
            'id': str(uuid.uuid4()),
            'messages': [{'role': 'user', 'content': conversation_prompt}],
            'model': self.model,
            'session_id': str(uuid.uuid4()),
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

    ai = Qwenlm(timeout=5000)
    response = ai.chat("Привет", stream=True)

    last_chunk = ""

    for chunk in response:
        last_chunk = chunk

    print(last_chunk)

    response = ai.chat("Привет, как дела?", stream=False)
    print(response)
