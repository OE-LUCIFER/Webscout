from uuid import uuid4
import requests
import json
import re
from typing import Any, Dict, Generator, Optional

from webscout.AIbase import AISearch
from webscout import exceptions
from webscout import LitAgent

class Response:
    """A wrapper class for DeepFind API responses.
    
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

class DeepFind(AISearch):
    """A class to interact with the DeepFind AI search API.
    
    DeepFind provides a powerful search interface that returns AI-generated responses
    based on web content. It supports both streaming and non-streaming responses.
    
    Basic Usage:
        >>> from webscout import DeepFind
        >>> ai = DeepFind()
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
        api_endpoint (str): The DeepFind API endpoint URL.
        stream_chunk_size (int): Size of chunks when streaming responses.
        timeout (int): Request timeout in seconds.
        headers (dict): HTTP headers used in requests.
    """

    def __init__(
        self,
        timeout: int = 30,
        proxies: Optional[dict] = None,
    ):
        """Initialize the DeepFind API client.
        
        Args:
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
            proxies (dict, optional): Proxy configuration for requests. Defaults to None.
        
        Example:
            >>> ai = DeepFind(timeout=60)  # Longer timeout
            >>> ai = DeepFind(proxies={'http': 'http://proxy.com:8080'})  # With proxy
        """
        self.session = requests.Session()
        self.api_endpoint = "https://www.deepfind.co/?q={query}"
        self.stream_chunk_size = 1024
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "Accept": "text/x-component",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "text/plain;charset=UTF-8",
            "DNT": "1",
            "Next-Action": "f354668f23f516a46ad0abe4dedb84b19068bb54",
            "Next-Router-State-Tree": '%5B%22%22%2C%7B%22children%22%3A%5B%22__PAGE__%3F%7B%5C%22q%5C%22%3A%5C%22hi%5C%22%7D%22%2C%7B%7D%2C%22%2F%3Fq%3Dhi%22%2C%22refresh%22%5D%7D%2Cnull%2Cnull%2Ctrue%5D',
            "Origin": "https://www.deepfind.co",
            "Referer": "https://www.deepfind.co/?q=hi",
            "Sec-Ch-Ua": '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": LitAgent().random(),
        }
        self.session.headers.update(self.headers)
        self.proxies = proxies

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
    ) -> Dict[str, Any] | Generator[str, None, None]:
        """Search using the DeepFind API and get AI-generated responses.
        
        This method sends a search query to DeepFind and returns the AI-generated response.
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
            >>> ai = DeepFind()
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
        url = self.api_endpoint.format(query=prompt)
        payload = [
            [{"role": "user", "id": uuid4().hex, "content": prompt}],
            uuid4().hex,
        ]

        def for_stream():
            try:
                with self.session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                ) as response:
                    response.raise_for_status()
                    streaming_text = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            content_matches = re.findall(r'"content":"([^"\\]*(?:\\.[^"\\]*)*)"', line)
                            if content_matches:
                                for content in content_matches:
                                    if len(content) > len(streaming_text):
                                        delta = content[len(streaming_text):]
                                        streaming_text = content
                                        delta = delta.replace('\\"', '"').replace('\\n', '\n')
                                        delta = re.sub(r'\[REF\]\(https?://[^\s]*\)', '', delta)
                                        if raw:
                                            yield {"text": delta}
                                        else:
                                            yield Response(delta)
                            description_matches = re.findall(r'"description":"([^"\\]*(?:\\.[^"\\]*)*)"', line)
                            if description_matches:
                                for description in description_matches:
                                    if description and len(description) > len(streaming_text):
                                        delta = description[len(streaming_text):]
                                        streaming_text = description
                                        delta = delta.replace('\\"', '"').replace('\\n', '\n')
                                        delta = re.sub(r'\[REF\]\(https?://[^\s]*\)', '', delta)
                                        if raw:
                                            yield {"text": f"{delta}\n"}
                                        else:
                                            yield Response(f"{delta}\n")
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

    @staticmethod
    def clean_content(text: str) -> str:
        """Removes all webblock elements with research or detail classes.
        
        Args:
            text (str): The text to clean
        
        Returns:
            str: The cleaned text
        
        Example:
            >>> text = '<webblock class="research">...</webblock>Other text'
            >>> cleaned_text = DeepFind.clean_content(text)
            >>> print(cleaned_text)
            Other text
        """
        cleaned_text = re.sub(
            r'<webblock class="(?:research|detail)">[^<]*</webblock>', "", text
        )
        return cleaned_text


if __name__ == "__main__":
    from rich import print
    ai = DeepFind()
    response = ai.search(input(">>> "), stream=True, raw=False)
    for chunk in response:
        print(chunk, end="", flush=True)