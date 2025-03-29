import json
from typing import Union, Any, Dict, Generator, Optional

import cloudscraper

from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions

class QwenLM(Provider):
    """
    A class to interact with the QwenLM API
    """

    AVAILABLE_MODELS = [
        "qwen-max-latest",
        "qwen-plus-latest",
        "qwen2.5-14b-instruct-1m",
        "qwq-32b",
        "qwen2.5-coder-32b-instruct",
        "qwen-turbo-latest",
        "qwen2.5-72b-instruct",
        "qwen2.5-vl-72b-instruct",
        "qvq-72b-preview"
    ]

    def __init__(
        self,
        cookies_path: str,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: Optional[str] = None,
        model: str = "qwen-plus-latest",
        system_prompt: str = "You are a helpful AI assistant."
    ):
        """Initializes the QwenLM API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}"
            )

        self.session = cloudscraper.create_scraper()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://chat.qwenlm.ai/api/chat/completions"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.cookies_path = cookies_path
        self.cookie_string, self.token = self._load_cookies()

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://chat.qwenlm.ai",
            "referer": "https://chat.qwenlm.ai/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
            "authorization": f"Bearer {self.token}" if self.token else '',
        }
        self.session.headers.update(self.headers)
        self.session.proxies = proxies
        self.chat_type = "t2t"  # search - used WEB, t2t - chatbot, t2i - image_gen
        if self.chat_type != "t2t":
            AVAILABLE_MODELS = [
                'qwen-plus-latest', 'qvq-72b-preview',
                'qvq-32b', 'qwen-turbo-latest',
                'qwen-max-latest'
            ]

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method))
            and not method.startswith("__")
        )
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

    def _load_cookies(self) -> tuple[str, str]:
        """Load cookies from a JSON file and build a cookie header string."""
        try:
            with open(self.cookies_path, "r") as f:
                cookies = json.load(f)
            cookie_string = "; ".join(
                f"{cookie['name']}={cookie['value']}" for cookie in cookies
            )
            token = next(
                (cookie.get("value") for cookie in cookies if cookie.get("name") == "token"),
                "",
            )
            return cookie_string, token
        except FileNotFoundError:
            raise exceptions.InvalidAuthenticationError(
                "Error: cookies.json file not found!"
            )
        except json.JSONDecodeError:
            raise exceptions.InvalidAuthenticationError(
                "Error: Invalid JSON format in cookies.json!"
            )

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator[Any, None, None]]:
        """Chat with AI."""

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {list(self.__available_optimizers)}"
                )

        payload = {
            'chat_type': self.chat_type,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ],
            "model": self.model,
            "stream": stream,
            "max_tokens": self.max_tokens_to_sample
        }

        def for_stream() -> Generator[Dict[str, Any], None, None]:
            response = self.session.post(
                self.api_endpoint, json=payload, headers=self.headers, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            cumulative_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        json_data = json.loads(data)
                        # Handle multiple response formats
                        if "choices" in json_data:
                            new_content = json_data.get("choices")[0].get("delta", {}).get("content", "")
                        elif "messages" in json_data:
                            assistant_msg = next(
                                (msg for msg in reversed(json_data["messages"]) if msg.get("role") == "assistant"),
                                {}
                            )
                            content_field = assistant_msg.get("content", "")
                            if isinstance(content_field, list):
                                new_content = "".join(item.get("text", "") for item in content_field)
                            else:
                                new_content = content_field
                        else:
                            new_content = ""
                        delta = new_content[len(cumulative_text):]
                        cumulative_text = new_content
                        if delta:
                            yield delta if raw else {"text": delta}
                    except json.JSONDecodeError:
                        continue
            self.last_response.update(dict(text=cumulative_text))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream() -> Dict[str, Any]:
            """
            Handles non-streaming responses by aggregating all streamed chunks into a single string.
            """

            # Initialize an empty string to accumulate the full response
            full_response = ""

            # Iterate through the stream generator and accumulate the text
            try:
                for response in self.ask(prompt, True, optimizer=optimizer, conversationally=conversationally):
                    if isinstance(response, dict):  # Check if the response is a dictionary
                        full_response += response.get("text", "")  # Extract and append the "text" field
                    elif isinstance(response, str):  # If the response is a string, directly append it
                        full_response += response
            except Exception as e:
                raise

            # Ensure last_response is updated with the aggregated text
            self.last_response.update({"text": full_response})

            # Update conversation history with the final response
            self.conversation.update_chat_history(prompt, self.get_message(self.last_response))

            return {"text": full_response}  # Return the dictionary containing the full response

        return for_stream() if stream else for_non_stream()


    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response string from chat."""

        def for_stream() -> Generator[str, None, None]:
            for response in self.ask(prompt, True, optimizer=optimizer, conversationally=conversationally):
                yield response if isinstance(response, str) else response["text"]

        def for_non_stream() -> str:
            result = self.ask(prompt, False, optimizer=optimizer, conversationally=conversationally)
            return self.get_message(result)

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Extracts the message content from a response dict."""
        assert isinstance(response, dict), "Response should be a dict"
        return response.get("text", "")

if __name__ == "__main__":
    from rich import print
    ai = QwenLM(cookies_path="cookies.json")
    response = ai.chat(input(">>> "), stream=False)
    ai.chat_type = "search" # search - used WEB, t2t - chatbot, t2i - image_gen
    print(response)
    # for chunk in response:
    #     print(chunk, end="", flush=True)
