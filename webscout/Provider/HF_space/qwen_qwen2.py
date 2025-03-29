from dataclasses import dataclass
from enum import Enum
import requests
import json
import re
import uuid
from typing import Union, List, Dict, Generator, Optional, Any, TypedDict, Final

# Type definitions
class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(TypedDict):
    role: str
    content: str

class APIResponse(TypedDict):
    event_id: str
    fn_index: int
    data: List[Any]

class StreamData(TypedDict):
    msg: str
    output: Dict[str, Any]

@dataclass
class APIConfig:
    url: Final[str] = "https://qwen-qwen2-72b-instruct.hf.space"
    api_endpoint: Final[str] = "https://qwen-qwen2-72b-instruct.hf.space/queue/join?"

@dataclass
class RequestHeaders:
    join: Dict[str, str]
    data: Dict[str, str]

    @classmethod
    def create_default(cls, base_url: str) -> 'RequestHeaders':
        common_headers = {
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        
        return cls(
            join={
                **common_headers,
                'accept': '*/*',
                'content-type': 'application/json',
                'origin': base_url,
                'referer': f'{base_url}/',
            },
            data={
                **common_headers,
                'accept': 'text/event-stream',
                'referer': f'{base_url}/',
            }
        )

class QwenAPI:
    def __init__(self, config: APIConfig = APIConfig()):
        self.config = config
        self.headers = RequestHeaders.create_default(config.url)

    @staticmethod
    def generate_session_hash() -> str:
        """Generate a unique session hash."""
        return str(uuid.uuid4()).replace('-', '')[:12]

    @staticmethod
    def format_prompt(messages: List[Message]) -> str:
        """
        Formats a list of messages into a single prompt string.

        Args:
            messages: A list of message dictionaries with "role" and "content" keys.

        Returns:
            str: The formatted prompt.
        """
        return "\n".join(f"{message['role']}: {message['content']}" for message in messages)

    def create_sync_generator(
        self,
        model: str,
        messages: List[Message],
        proxy: Optional[str] = None,
        **kwargs: Any
    ) -> Generator[str, None, None]:
        """
        Synchronously streams responses from the Qwen_Qwen2_72B_Instruct API.

        Args:
            model: The model to use for the request.
            messages: A list of message dictionaries with "role" and "content" keys.
            proxy: Optional proxy URL for the request.
            **kwargs: Additional keyword arguments.

        Yields:
            str: Text chunks from the API response.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
            json.JSONDecodeError: If the response cannot be parsed as JSON.
        """
        session_hash: str = self.generate_session_hash()

        # Prepare the prompt
        system_messages: List[str] = [
            message["content"] 
            for message in messages 
            if message["role"] == Role.SYSTEM.value
        ]
        system_prompt: str = "\n".join(system_messages)
        
        user_messages: List[Message] = [
            message 
            for message in messages 
            if message["role"] != Role.SYSTEM.value
        ]
        prompt: str = self.format_prompt(user_messages)

        payload_join: Dict[str, Any] = {
            "data": [prompt, [], system_prompt],
            "event_data": None,
            "fn_index": 0,
            "trigger_id": 11,
            "session_hash": session_hash
        }

        with requests.Session() as session:
            # Send join request
            response = session.post(
                self.config.api_endpoint,
                headers=self.headers.join,
                json=payload_join
            )
            response.raise_for_status()
            event_data: APIResponse = response.json()

            # Prepare data stream request
            url_data: str = f'{self.config.url}/queue/data'
            params_data: Dict[str, str] = {'session_hash': session_hash}

            # Send data stream request
            full_response: str = ""
            final_full_response: str = ""

            with session.get(
                url_data,
                headers=self.headers.data,
                params=params_data,
                stream=True
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        decoded_line: str = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            try:
                                json_data: StreamData = json.loads(decoded_line[6:])

                                if json_data.get('msg') == 'process_generating':
                                    if 'output' in json_data and 'data' in json_data['output']:
                                        output_data: List[Any] = json_data['output']['data']
                                        if len(output_data) > 1 and len(output_data[1]) > 0:
                                            for item in output_data[1]:
                                                if isinstance(item, list) and len(item) > 1:
                                                    fragment: str = str(item[1])
                                                    if not re.match(r'^\[.*\]$', fragment) and not full_response.endswith(fragment):
                                                        full_response += fragment
                                                        yield fragment

                                if json_data.get('msg') == 'process_completed':
                                    if 'output' in json_data and 'data' in json_data['output']:
                                        output_data = json_data['output']['data']
                                        if len(output_data) > 1 and len(output_data[1]) > 0:
                                            final_full_response = output_data[1][0][1]
                                            
                                            if final_full_response.startswith(full_response):
                                                final_full_response = final_full_response[len(full_response):]
                                            
                                            if final_full_response:
                                                yield final_full_response
                                        break

                            except json.JSONDecodeError as e:
                                print(f"Could not parse JSON: {decoded_line}")
                                raise e


def main() -> None:
    messages: List[Message] = [
        {"role": Role.SYSTEM.value, "content": "You are a helpful assistant."},
        {"role": Role.USER.value, "content": "LOL"}
    ]

    api = QwenAPI()
    for text in api.create_sync_generator("qwen-qwen2-72b-instruct", messages):
        print(text, end="", flush=True)
    print("\n---\n")


if __name__ == "__main__":
    main()