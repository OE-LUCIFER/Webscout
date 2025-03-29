import requests
from uuid import uuid4
import json
from typing import Any, Dict, Generator, Optional

from webscout.AIbase import AISearch
from webscout import exceptions
from webscout import LitAgent


class Response:
    """A wrapper class for Felo API responses.
    
    This class automatically converts response objects to their text representation
    when printed or converted to string.
    
    Attributes:
        text (str): The text content of the response
        
    Example:
        >>> response = Response("Hello, world!")
        >>> print(response)
        Hello, world!
        >>> str(response)
        'Hello, world!'
    """
    def __init__(self, text: str):
        self.text = text
    
    def __str__(self):
        return self.text
    
    def __repr__(self):
        return self.text


class Felo(AISearch):
    """A class to interact with the Felo AI search API.
    
    Felo provides a powerful search interface that returns AI-generated responses
    based on web content. It supports both streaming and non-streaming responses.
    
    Basic Usage:
        >>> from webscout import Felo
        >>> ai = Felo()
        >>> # Non-streaming example
        >>> response = ai.search("What is Python?")
        >>> print(response)
        Python is a high-level programming language...
        
        >>> # Streaming example
        >>> for chunk in ai.search("Tell me about AI", stream=True):
        ...     print(chunk, end="", flush=True)
        Artificial Intelligence is...
        
        >>> # Raw response format
        >>> for chunk in ai.search("Hello", stream=True, raw=True):
        ...     print(chunk)
        {'text': 'Hello'}
        {'text': ' there!'}
    
    Args:
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
        proxies (dict, optional): Proxy configuration for requests. Defaults to None.
    
    Attributes:
        api_endpoint (str): The Felo API endpoint URL.
        stream_chunk_size (int): Size of chunks when streaming responses.
        timeout (int): Request timeout in seconds.
        headers (dict): HTTP headers used in requests.
    """

    def __init__(
        self,
        timeout: int = 30,
        proxies: Optional[dict] = None,
    ):
        """Initialize the Felo API client.
        
        Args:
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
            proxies (dict, optional): Proxy configuration for requests. Defaults to None.
        
        Example:
            >>> ai = Felo(timeout=60)  # Longer timeout
            >>> ai = Felo(proxies={'http': 'http://proxy.com:8080'})  # With proxy
        """
        self.session = requests.Session()
        self.chat_endpoint = "https://api.felo.ai/search/threads"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "cookie": "_clck=1gifk45%7C2%7Cfoa%7C0%7C1686; _clsk=1g5lv07%7C1723558310439%7C1%7C1%7Cu.clarity.ms%2Fcollect; _ga=GA1.1.877307181.1723558313; _ga_8SZPRV97HV=GS1.1.1723558313.1.1.1723558341.0.0.0; _ga_Q9Q1E734CC=GS1.1.1723558313.1.1.1723558341.0.0.0",
            "dnt": "1",
            "origin": "https://felo.ai",
            "referer": "https://felo.ai/",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": LitAgent().random()
        }
        self.session.headers.update(self.headers)
        self.proxies = proxies

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
    ) -> Union[Dict[str, Any], Generator[Any, None, None]][str, None, None]:
        """Search using the Felo API and get AI-generated responses.
        
        This method sends a search query to Felo and returns the AI-generated response.
        It supports both streaming and non-streaming modes, as well as raw response format.
        
        Args:
            prompt (str): The search query or prompt to send to the API.
            stream (bool, optional): If True, yields response chunks as they arrive.
                                   If False, returns complete response. Defaults to False.
            raw (bool, optional): If True, returns raw response dictionaries with 'text' key.
                                If False, returns Response objects that convert to text automatically.
                                Defaults to False.
        
        Returns:
            Union[Dict[str, Any], Generator[str, None, None]]: 
                - If stream=False: Returns complete response
                - If stream=True: Yields response chunks as they arrive
        
        Raises:
            APIConnectionError: If the API request fails
        
        Examples:
            Basic search:
            >>> ai = Felo()
            >>> response = ai.search("What is Python?")
            >>> print(response)
            Python is a programming language...
            
            Streaming response:
            >>> for chunk in ai.search("Tell me about AI", stream=True):
            ...     print(chunk, end="")
            Artificial Intelligence...
            
            Raw response format:
            >>> for chunk in ai.search("Hello", stream=True, raw=True):
            ...     print(chunk)
            {'text': 'Hello'}
            {'text': ' there!'}
            
            Error handling:
            >>> try:
            ...     response = ai.search("My question")
            ... except exceptions.APIConnectionError as e:
            ...     print(f"API error: {e}")
        """
        payload = {
            "query": prompt,
            "search_uuid": uuid4().hex,
            "lang": "",
            "agent_lang": "en",
            "search_options": {
                "langcode": "en-US"
            },
            "search_video": True,
            "contexts_from": "google"
        }

        def for_stream():
            try:
                with self.session.post(
                    self.chat_endpoint,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                ) as response:
                    if not response.ok:
                        raise exceptions.APIConnectionError(
                            f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                        )

                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line.startswith('data:'):
                            try:
                                data = json.loads(line[5:].strip())
                                if data['type'] == 'answer' and 'text' in data['data']:
                                    new_text = data['data']['text']
                                    if len(new_text) > len(streaming_text):
                                        delta = new_text[len(streaming_text):]
                                        streaming_text = new_text
                                        if raw:
                                            yield {"text": delta}
                                        else:
                                            yield Response(delta)
                            except json.JSONDecodeError:
                                pass
                    self.last_response = Response(streaming_text)
            except requests.exceptions.RequestException as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        def for_non_stream():
            full_response = ""
            for chunk in for_stream():
                if raw:
                    yield chunk
                else:
                    full_response += str(chunk)
            if not raw:
                self.last_response = Response(full_response)
                return self.last_response
        
        return for_stream() if stream else for_non_stream()


if __name__ == "__main__":
    from rich import print
    ai = Felo()
    response = ai.search(input(">>> "), stream=True, raw=False)
    for chunk in response:
        print(chunk, end="", flush=True)
