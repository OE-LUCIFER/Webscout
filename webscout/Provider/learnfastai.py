import os
import json
from typing import Optional, Union, Generator
import uuid
import requests
import cloudscraper

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions


class LearnFast(Provider):
    """
    A class to interact with the LearnFast.ai API.
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
        Initializes the LearnFast.ai API with given parameters.
        """
        self.session = cloudscraper.create_scraper()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = 'https://autosite.erweima.ai/api/v1/chat'
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.headers = {
            "authority": "autosite.erweima.ai",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "authorization": "",  # Always empty
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://learnfast.ai",
            "priority": "u=1, i",
            "referer": "https://learnfast.ai/",
            "sec-ch-ua": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
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

    def generate_unique_id(self) -> str:
        """Generate a 32-character hexadecimal unique ID."""
        return uuid.uuid4().hex

    def generate_session_id(self) -> str:
        """Generate a 32-character hexadecimal session ID."""
        return uuid.uuid4().hex

    def upload_image_to_0x0(self, image_path: str) -> str:
        """
        Uploads an image to 0x0.st and returns the public URL.
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"The file '{image_path}' does not exist.")

        with open(image_path, "rb") as img_file:
            files = {"file": img_file}
            try:
                response = requests.post("https://0x0.st", files=files)
                response.raise_for_status()
                image_url = response.text.strip()
                if not image_url.startswith("http"):
                    raise ValueError("Received an invalid URL from 0x0.st.")
                return image_url
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to upload image to 0x0.st: {e}") from e

    def create_payload(
        self,
        session_id: str,
        conversation_prompt: str,
        image_url: Optional[str] = None
    ) -> dict:
        """
        Creates the JSON payload for the request.
        """
        payload = {
            "prompt": conversation_prompt,
            "firstQuestionFlag": True,
            "sessionId": session_id,
            "attachments": []
        }
        if image_url:
            payload["attachments"] = [
                {
                    "fileType": "image/jpeg",
                    "file": {},
                    "fileContent": image_url
                }
            ]
        return payload

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        image_path: Optional[str] = None,
    ) -> Union[dict, Generator[dict, None, None]]:
        """Chat with LearnFast

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            image_path (Optional[str], optional): Path to the image to be uploaded.
                                                 Defaults to None.

        Returns:
           Union[dict, Generator[dict, None, None]]: Response generated
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

        # Generate unique ID and session ID
        unique_id = self.generate_unique_id()
        session_id = self.generate_session_id()

        # Update headers with the unique ID
        self.headers["uniqueid"] = unique_id

        # Upload image and get URL if image_path is provided
        image_url = None
        if image_path:
            try:
                image_url = self.upload_image_to_0x0(image_path)
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Error uploading image: {e}") from e

        # Create the payload
        payload = self.create_payload(session_id, conversation_prompt, image_url)

        # Convert the payload to a JSON string
        data = json.dumps(payload)

        try:
            # Send the POST request with streaming enabled
            response = self.session.post(self.api_endpoint, headers=self.headers, data=data, stream=True, timeout=self.timeout)
            response.raise_for_status()  # Check for HTTP errors

            # Process the streamed response
            full_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    line = line.strip()
                    if line == "[DONE]":
                        break
                    try:
                        json_response = json.loads(line)
                        if json_response.get('code') == 200 and json_response.get('data'):
                            message = json_response['data'].get('message', '')
                            if message:
                                full_response += message
                                if stream:
                                    yield {"text": message}
                    except json.JSONDecodeError:
                        pass
            self.last_response.update({"text": full_response})
            self.conversation.update_chat_history(prompt, full_response)

            if not stream:
                return self.last_response
        except requests.exceptions.RequestException as e:
            raise exceptions.FailedToGenerateResponseError(f"An error occurred: {e}")

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        image_path: Optional[str] = None,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            image_path (Optional[str], optional): Path to the image to be uploaded.
                                                 Defaults to None.
        Returns:
            Union[str, Generator[str, None, None]]: Response generated
        """
        try:
            response = self.ask(prompt, stream, optimizer=optimizer, conversationally=conversationally, image_path=image_path)
            if stream:
                for chunk in response:
                    yield chunk["text"]
            else:
                return str(response)
        except Exception as e:
            return f"Error: {str(e)}"

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
    ai = LearnFast()
    response = ai.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)