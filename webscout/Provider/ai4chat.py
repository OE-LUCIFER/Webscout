import requests
import json
import html
import re
from typing import Union, Any, Dict

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider

class AI4Chat(Provider):
    """
    A class to interact with the AI4Chat API.
    """

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
        system_prompt: str = "You are a helpful and informative AI assistant.",
    ) -> None:
        """
        Initializes the AI4Chat API with given parameters.

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
            system_prompt (str, optional): System prompt to guide the AI's behavior. Defaults to "You are a helpful and informative AI assistant.".
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://www.ai4chat.co/generate-response"
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "authority": "www.ai4chat.co",
            "method": "POST",
            "path": "/generate-response",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "cookie": "messageCount=1",
            "dnt": "1",
            "origin": "https://www.ai4chat.co",
            "priority": "u=1, i",
            "referer": "https://www.ai4chat.co/gpt/talkdirtytome",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0"
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
        """
        Sends a prompt to the AI4Chat API and returns the response.

        Args:
            prompt: The text prompt to generate text from.
            stream (bool, optional): Not used (AI4Chat doesn't support streaming).
            raw (bool, optional): Whether to return the raw response. Defaults to False.
            optimizer (str, optional): The name of the optimizer to use. Defaults to None.
            conversationally (bool, optional): Whether to chat conversationally. Defaults to False.

        Returns:
            dict: A dictionary containing the AI's response.
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
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ]
        }

        response = self.session.post(self.api_endpoint, headers=self.headers, json=payload, timeout=self.timeout)
        if not response.ok:
            raise Exception(f"Failed to generate response: {response.status_code} - {response.reason}")
        
        response_data = response.json()
        message_content = response_data.get('message', 'No message found')

        # Decode HTML entities
        decoded_message = html.unescape(message_content)

        # Remove HTML tags while preserving newlines and list structure
        cleaned_text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', decoded_message)
        cleaned_text = re.sub(r'<ol>|</ol>', '', cleaned_text)
        cleaned_text = re.sub(r'<li><p>(.*?)</p></li>', r'• \1\n', cleaned_text)
        cleaned_text = re.sub(r'</?[^>]+>', '', cleaned_text)
        
        # Remove extra newlines
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text.strip())

        self.last_response.update(dict(text=cleaned_text))
        self.conversation.update_chat_history(prompt, cleaned_text)
        return self.last_response

    def chat(
        self,
        prompt: str,
        stream: bool = False,  # Streaming is not supported by AI4Chat
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """
        Generates a response from the AI4Chat API.

        Args:
            prompt (str): The prompt to send to the AI.
            stream (bool, optional): Not used (AI4Chat doesn't support streaming). 
            optimizer (str, optional): The name of the optimizer to use. Defaults to None.
            conversationally (bool, optional): Whether to chat conversationally. Defaults to False.

        Returns:
            str: The response generated by the AI.
        """
        return self.get_message(
            self.ask(
                prompt,
                optimizer=optimizer,
                conversationally=conversationally,
            )
        )

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    ai = AI4Chat() 
    response = ai.chat("write me poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)