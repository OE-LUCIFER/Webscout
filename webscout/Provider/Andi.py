from uuid import uuid4
import requests
import json
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import WEBS
from rich import print


class AndiSearch(Provider):
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
        """Instantiates AndiSearch

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
        """
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://write.andisearch.com/v1/write_streaming"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "accept": "text/event-stream",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "andi-auth-key": "andi-summarizer",
            "andi-origin": "x-andi-origin",
            "authorization": str(uuid4()),
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://andisearch.com",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
            "x-amz-date": "20240730T031106Z",
            "x-amz-security-token": str(uuid4()),
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

        # Initialize the webscout instance
        webs = WEBS()

        # Fetch search results
        search_query = prompt
        search_results = webs.text(search_query, max_results=7)

        # Format the search results into the required serp payload structure
        serp_payload = {
            "query": search_query,
            "serp": {
                "results_type": "Search",
                "answer": "",
                "type": "navigation",
                "title": "",
                "description": "",
                "image": "",
                "link": "",
                "source": "liftndrift.com",
                "engine": "andi-b",
                "results": [
                    {
                        "title": result["title"],
                        "link": result["href"],
                        "desc": result["body"],
                        "image": "",
                        "type": "website",
                        "source": result["href"]
                        .split("//")[1]
                        .split("/")[0],  # Extract the domain name
                    }
                    for result in search_results
                ],
            },
        }
        self.session.headers.update(self.headers)
        payload = serp_payload

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_text = ""
            for value in response.iter_lines(
                decode_unicode=True,
                chunk_size=self.stream_chunk_size,
                delimiter="\n",
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
        return response["text"]


if __name__ == "__main__":
    from rich import print

    ai = AndiSearch()
    response = ai.chat("tell me about india")
    for chunk in response:
        print(chunk, end="", flush=True)
