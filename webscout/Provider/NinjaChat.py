import requests
import json
import os
from typing import Any, Dict, Optional, Generator, List, Union

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions


class NinjaChat(Provider):
    """
    A class to interact with the NinjaChat API.
    """

    AVAILABLE_MODELS = {
        "mistral": "https://www.ninjachat.ai/api/mistral",
        "perplexity": "https://www.ninjachat.ai/api/perplexity",
        "claude-3.5": "https://www.ninjachat.ai/api/claude-pro",
        "gemini-1.5-pro": "https://www.ninjachat.ai/api/gemini",
        "llama": "https://www.ninjachat.ai/api/llama-pro",
        "o1-mini": "https://www.ninjachat.ai/api/o1-mini",
    }

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: str = None,  # System message/intro prompt
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "perplexity",  # Default model
        system_message: str = "You are a helpful AI assistant.",  # Default system message
    ):
        """Initializes the NinjaChat API client."""

        self.headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
                "Content-Type": "application/json",
                "Cookie": "_ga=GA1.1.298084589.1727859540; _ga_11N4NZX9WP=GS1.1.1727859539.1.0.1727859552.0.0.0; __stripe_mid=4f63db68-c41d-45b4-9111-2457a6cf1b538696a9; __Host-next-auth.csrf-token=a5cb5a40c73df3e808ebc072dcb116fe7dd4b9b8d39d8002ef7e54153e6aa665%7Cbffe3f934f2db43330d281453af2cd0b4757f439b958f2d1a06a36cea63e9cc8; __stripe_sid=118678d1-403a-43f9-b3b9-d80ed9392a0d2ac131; __Secure-next-auth.callback-url=https%3A%2F%2Fwww.ninjachat.ai%2Fdashboard; __Secure-next-auth.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..l34CIFGTJCtstUqU.VjEYgaUUPpgp-49wueXFlFYvbm8csuyX0HichHrPNH45nX4s_LeZX2VhK1ZvwmUpfdlsMD4bi8VzFfQUEgs8FLPhkbKnoZDP939vobV7K_2Q9CA8PgC0oXEsQf_azWmILZ8rOE37uYzTu1evCnOjCucDYrC1ONXzl9NbGNPVa8AQr7hXvatuqtqe-lBUQXWdrw3QLulbqxvh6yLoxJj04gqC-nPudGciU-_-3TZJYr98u8o7KtUGio1ZX9vHNFfv8djWM1NCkji3Kl9eUhiyMj71.6uhUS39UcCVRa6tFzHxz2g; ph_phc_wWUtqcGWqyyochfPvwKlXMkMjIoIQKUwcnHE3KMKm8K_posthog=%7B%22distinct_id%22%3A%2201924c74-2926-7042-a1fb-5b5debdbcd1c%22%2C%22%24sesid%22%3A%5B1727966419499%2C%22019252bb-9de4-75db-9f85-a389fb401670%22%2C1727964880355%5D%7D",
                "DNT": "1",
                "Origin": "https://www.ninjachat.ai",
                "Priority": "u=1, i",
                "Referer": "https://www.ninjachat.ai/dashboard",
                "Sec-CH-UA": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
                )
    }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(proxies)
        self.timeout = timeout
        self.last_response = {}
        self.system_message = system_message

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        
        #Set the intro/system message
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or system_message or Conversation.intro #Priority: act > intro > system_message > Conversation.intro

        )


        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {', '.join(self.AVAILABLE_MODELS)}")
        self.model_url = self.AVAILABLE_MODELS[model]
        self.headers["Referer"] = self.model_url  # Set initial referer



    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict, Generator]:

        conversation_prompt = self.conversation.gen_complete_prompt(prompt, intro=Conversation.intro)

        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        #Include the system message in the payload
        payload = {
            "messages": [
                {"role": "system", "content": self.system_message}, # System message here
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream  # Now passed dynamically
        }

        def for_stream():
            try:
                with requests.post(self.model_url, headers=self.headers, json=payload, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()
                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            if line.startswith("0:"):
                                try:
                                    text = json.loads(line[2:]) # Extract streaming text
                                    streaming_text += text #Accumulate for history
                                    resp = dict(text=text)
                                    yield resp if raw else resp
                                except json.JSONDecodeError:
                                    print("\n[Error] Failed to decode JSON content.")

                            elif line.startswith("d:"):
                                break #End of stream
                    self.conversation.update_chat_history(prompt, streaming_text)
                    self.last_response.update({"text": streaming_text})
            except requests.exceptions.RequestException as e:
                print("An error occurred:", e)



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
    ) -> Union[str, Generator]:

        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt, False, optimizer=optimizer, conversationally=conversationally
                )
            )
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]



if __name__ == "__main__":
    from rich import print
    bot = NinjaChat(model="perplexity", system_message="You are a creative writer.")

    response = bot.chat("tell me about Abhay koul, HelpingAI ", stream=True)

    for chunk in response:
        print(chunk, end="", flush=True)
