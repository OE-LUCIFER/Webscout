import requests
import json

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider

class GPTWeb(Provider):
    """
    A class to interact with the Nexra GPTWeb API.
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

    ):
        """
        Initializes the Nexra GPTWeb API with given parameters.

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
            system_prompt (str, optional): System prompt for GPTWeb. Defaults to "You are a helpful AI assistant.".
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = 'https://nexra.aryahcr.cc/api/chat/gptweb'
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Content-Type": "application/json"
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
        """Chat with GPTWeb

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

        data = {
            "prompt": conversation_prompt,
            "markdown": False
        }

        def for_stream():
            response = self.session.post(self.api_endpoint, headers=self.headers, data=json.dumps(data), stream=True, timeout=self.timeout)
            if not response.ok:
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )
            
            full_response = ''
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    line = line.lstrip('_') # Remove "_"
                    try:
                        # Attempt to parse the entire line as JSON
                        json_data = json.loads(line)  
                        full_response = json_data.get("gpt", "")
                        yield full_response if raw else dict(text=full_response) 
                    except json.JSONDecodeError:
                        print(f"Skipping invalid JSON line: {line}") 
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
        return response["text"]

if __name__ == '__main__':
    from rich import print
    ai = GPTWeb()
    response = ai.chat("tell me about Abhay koul, HelpingAI", stream=True)
    for chunk in response:
        print(chunk, end='', flush=True)