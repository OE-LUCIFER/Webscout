import requests
import json
from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions

class AIUncensored(Provider):
    """
    A class to interact with the AIUncensored.info API.
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
        Initializes the AIUncensored.info API with given parameters.
        
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
            system_prompt (str, optional): System prompt for AIUncensored.
                                        Defaults to "You are a helpful AI assistant.".
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = 'https://twitterclone-i0wr.onrender.com/api/chat'
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.headers = {
            "authority": "twitterclone-i0wr.onrender.com",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://www.aiuncensored.info",
            "priority": "u=1, i",
            "referer": "https://www.aiuncensored.info/",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
        }

        self.__available_optimizers = [
            method for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        ]
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
    ):
        """
        Chat with AI

        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.

        Returns:
           dict or generator: 
           If stream is False, returns a dict:
           ```json
           {
              "text" : "How may I assist you today?"
           }
           ```
           If stream is True, yields dicts with incremental text.
        """

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)


        if optimizer:

            if optimizer in self.__available_optimizers:
                try:
                    conversation_prompt = getattr(Optimizers, optimizer)(
                        conversation_prompt if conversationally else prompt
                    )

                except Exception as e:

                    raise
            else:

                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": conversation_prompt
                }
            ]
        }



        def for_stream():
            with requests.post(self.api_endpoint, headers=self.headers, json=payload, stream=True, timeout=self.timeout) as response:

                if response.status_code == 200:
                    full_content = ''
                    for line in response.iter_lines():
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line:

                            if decoded_line == "data: [DONE]":

                                break
                            if decoded_line.startswith("data: "):
                                data_str = decoded_line[len("data: "):]  
                                try:
                                    data_json = json.loads(data_str)
                                    content = data_json.get("data", "")
                                    if content:
                                        full_content += content
                                        yield content if raw else dict(text=content)
                                except json.JSONDecodeError:
                                    raise Exception
                self.last_response.update(dict(text=full_content))
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
    ):
        """
        Generate response `str`
        Args:
            prompt (str): Prompt to be sent.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str or generator: 
            If stream is False, returns a string.
            If stream is True, yields incremental strings.
        """

        def for_stream():

            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            ):

                yield self.get_message(response)

        def for_non_stream():

            response = self.ask(
                prompt,
                False,
                optimizer=optimizer,
                conversationally=conversationally,
            )

            return self.get_message(response)

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

if __name__ == "__main__":
    from rich import print
    ai = AIUncensored(timeout=5000)
    response = ai.chat("write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)