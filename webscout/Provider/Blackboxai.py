import requests
import re
import json
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts


# ------------------------------------------------------BLACKBOXAI--------------------------------------------------------
class BLACKBOXAI:
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 8000,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = None,
    ):
        """Instantiates BLACKBOXAI

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): Model name. Defaults to "Phind Model".
        """
        self.session = requests.Session()
        self.max_tokens_to_sample = max_tokens
        self.is_conversation = is_conversation
        self.chat_endpoint = "https://api.blackbox.ai/api/chat"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.previewToken: str = None
        self.userId: str = ""
        self.codeModelMode: bool = True
        self.id: str = ""
        self.agentMode: dict = {}
        self.trendingAgentMode: dict = {}
        self.isMicMode: bool = False

        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "",
            "Accept": "*/*",
            "Accept-Encoding": "Identity",
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
           "text" : "print('How may I help you today?')"
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

        self.session.headers.update(self.headers)
        payload = {
            "messages": [
                # json.loads(prev_messages),
                {"content": conversation_prompt, "role": "user"}
            ],
            "id": self.id,
            "previewToken": self.previewToken,
            "userId": self.userId,
            "codeModelMode": self.codeModelMode,
            "agentMode": self.agentMode,
            "trendingAgentMode": self.trendingAgentMode,
            "isMicMode": self.isMicMode,
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if (
                not response.ok
                or not response.headers.get("Content-Type")
                == "text/plain; charset=utf-8"
            ):
                raise Exception(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )
            streaming_text = ""
            for value in response.iter_lines(
                decode_unicode=True,
                chunk_size=self.stream_chunk_size,
            ):
                try:
                    if bool(value):
                        streaming_text += value + ("\n" if stream else "")

                        resp = dict(text=streaming_text)
                        self.last_response.update(resp)
                        yield value if raw else resp
                except json.decoder.JSONDecodeError:
                    pass
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
        return response["text"].replace("\\n", "\n").replace("\\n\\n", "\n\n")


# Function to clean the response text
def clean_response(response_text: str) -> str:
    # Remove web search results
    cleaned_response = re.sub(r"\$~~~\$.*?\$~~~\$", "", response_text, flags=re.DOTALL)
    # Remove any remaining special characters or markers
    cleaned_response = re.sub(r"\$~~~", "", cleaned_response)
    return cleaned_response.strip()


if __name__ == "__main__":
    from rich import print

    ai = BLACKBOXAI()
    response = ai.chat("tell me about india")
    for chunk in response:
        print(chunk, end="", flush=True)
