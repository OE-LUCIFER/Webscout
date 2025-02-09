from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
import requests


class Chatify(Provider):
    """
    A class to interact with the Chatify AI API.
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
    ):
        """
        Initializes the Chatify AI API with given parameters.
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://chatify-ai.vercel.app/api/chat"
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://chatify-ai.vercel.app",
            "Referer": "https://chatify-ai.vercel.app/",
            "Sec-CH-UA": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
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
    ) -> dict:
        """
        Sends a prompt to the Chatify API and returns the response.
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

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": conversation_prompt})

        payload = {"messages": messages}

        def for_stream():
            response = self.session.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=self.timeout,
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_text = ""
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")  # Decode the line
                    parts = decoded_line.split(":", 1)
                    if len(parts) > 1:
                        content = parts[1].strip().strip('"')
                        streaming_text += content
                        yield content if raw else dict(text=content)
            self.last_response.update(dict(text=streaming_text))
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
        """
        Generates a response from the Chatify API.
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
        """
        Extracts the message from the API response and formats it.
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"].replace("\\n", "\n").replace("\\n\\n", "\n\n")


# Example usage
if __name__ == "__main__":
    from rich import print

    ai = Chatify(timeout=5000)
    response = ai.chat("write a poem about AI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
