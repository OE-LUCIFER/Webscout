import requests
import uuid
import json

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider

class Roboclinic(Provider):
    """
    A class to interact with the Roboclinic.ai API.
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
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """
        Initializes the Roboclinic.ai API with given parameters.

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
            system_prompt (str, optional): System prompt for Roboclinic.ai. 
                                   Defaults to "You are a helpful AI assistant.".
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://api.roboclinic.ai/api"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://roboclinic.ai",
            "referer": "https://roboclinic.ai/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
            "dnt": "1",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
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
    ) -> dict:
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

        conversation_id = str(uuid.uuid4()).replace('-', '')[:20]

        # Step 1: Create a new chat
        create_chat_url = f"{self.api_endpoint}/without-auth-chat/create-chat/"
        create_chat_data = {
            "conversation_id": conversation_id,
            "name": "New chat"
        }

        response = self.session.post(create_chat_url, headers=self.headers, json=create_chat_data)
        if response.status_code != 201:
            raise Exception(
                f"Failed to create chat: {response.status_code} - {response.text}"
            )

        # Step 2: Send a message to the chat
        send_message_url = f"{self.api_endpoint}/without-auth-chat/send-message/"
        send_message_data = {
            "conversation_id": conversation_id,
            "message": conversation_prompt,
            "model": "gpt-4o",
            "chat": None
        }

        response = self.session.post(send_message_url, headers=self.headers, json=send_message_data)
        if response.status_code != 201:
            raise Exception(
                f"Failed to send message: {response.status_code} - {response.text}"
            )

        # Step 3: Retrieve and stream the GPT-4 response
        get_gpt_answer_url = f"{self.api_endpoint}/chats/get-gpt-answer/{conversation_id}/"

        def for_stream():
            with requests.get(get_gpt_answer_url, headers=self.headers, stream=True) as response:
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to retrieve GPT-4 response: {response.status_code} - {response.text}"
                    )
                full_response = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        if line.startswith("data:"):
                            start = line.find('"value": "') + 10
                            end = line.find('"', start)
                            if start != -1 and end != -1:
                                chunk = line[start:end]
                                full_response += chunk
                                yield chunk if raw else dict(text=full_response)
                self.last_response.update(dict(text=full_response))
                self.conversation.update_chat_history(
                    prompt, self.get_message(self.last_response)
                )

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
        return response["text"].replace('\\n', '\n').replace('\\n\\n', '\n\n')


if __name__ == "__main__":
    from rich import print

    ai = Roboclinic()
    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)