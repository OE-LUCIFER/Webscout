import cloudscraper
from uuid import uuid4
import json
import re
from typing import Dict, Optional, Generator, Union, Any

from webscout.AIbase import AISearch
from webscout import exceptions
from webscout import LitAgent


class Response:
    """A wrapper class for Genspark API responses.
    
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


class Genspark(AISearch):
    """A class to interact with the Genspark AI search API.
    
    Genspark provides a powerful search interface that returns AI-generated responses
    based on web content. It supports both streaming and non-streaming responses.
    
    Basic Usage:
        >>> from webscout import Genspark
        >>> ai = Genspark()
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
        max_tokens (int, optional): Maximum tokens to generate. Defaults to 600.
    """

    def __init__(
        self,
        timeout: int = 30,
        proxies: Optional[dict] = None,
        max_tokens: int = 600,
    ):
        """Initialize the Genspark API client.
        
        Args:
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
            proxies (dict, optional): Proxy configuration for requests. Defaults to None.
            max_tokens (int, optional): Maximum tokens to generate. Defaults to 600.
        """
        self.session = cloudscraper.create_scraper()
        self.max_tokens = max_tokens
        self.chat_endpoint = "https://www.genspark.ai/api/search/stream"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://www.genspark.ai",
            "Priority": "u=1, i",
            "Sec-CH-UA": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": LitAgent().random(),
        }
        
        self.cookies = {
            "i18n_redirected": "en-US",
            "agree_terms": "0",
            "session_id": uuid4().hex,
        }

        self.session.headers.update(self.headers)
        self.session.proxies = proxies or {}

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
    ) -> Union[Dict[str, Any], Generator[Union[Dict[str, Any], str], None, None]]:
        """Search using the Genspark API and get AI-generated responses.
        
        Args:
            prompt (str): The search query or prompt to send to the API.
            stream (bool, optional): If True, yields response chunks as they arrive.
                                   If False, returns complete response. Defaults to False.
            raw (bool, optional): If True, returns raw response dictionaries with 'text' key.
                                If False, returns Response objects that convert to text automatically.
                                Defaults to False.
        
        Returns:
            Union[Dict[str, Any], Generator[Union[Dict[str, Any], str], None, None]]: 
                - If stream=False: Returns complete response
                - If stream=True: Yields response chunks as they arrive
        
        Raises:
            APIConnectionError: If the API request fails
        """
        url = f"https://www.genspark.ai/api/search/stream?query={prompt.replace(' ', '%20')}"
        
        def for_stream():
            try:
                with self.session.post(
                    url,
                    headers=self.headers,
                    cookies=self.cookies,
                    json={},  # Empty payload as query is in URL
                    stream=True,
                    timeout=self.timeout,
                ) as response:
                    if not response.ok:
                        raise exceptions.APIConnectionError(
                            f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                        )
                    
                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if "field_name" in data and "delta" in data:
                                    if data["field_name"].startswith("streaming_detail_answer"):
                                        delta_text = data.get("delta", "")
                                        
                                        # Clean up markdown links in text
                                        delta_text = re.sub(r"\[.*?\]\(.*?\)", "", delta_text)
                                        
                                        if raw:
                                            yield {"text": delta_text}
                                        else:
                                            yield Response(delta_text)
                            except json.JSONDecodeError:
                                continue
                                
            except cloudscraper.exceptions as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")
                
        def for_non_stream():
            full_response = ""
            for chunk in for_stream():
                if raw:
                    yield chunk
                else:
                    full_response += str(chunk)
            
            if not raw:
                # Process the full response to clean up any JSON structures
                try:
                    text_json = json.loads(full_response)
                    if isinstance(text_json, dict) and "detailAnswer" in text_json:
                        full_response = text_json.get("detailAnswer", full_response)
                except (json.JSONDecodeError, TypeError):
                    # Not valid JSON or not a dictionary, keep as is
                    pass
                    
                self.last_response = Response(full_response)
                return self.last_response

        return for_stream() if stream else for_non_stream()


if __name__ == "__main__":

    from rich import print
    
    ai = Genspark()
    response = ai.search(input(">>> "), stream=True, raw=False)
    for chunk in response:
        print(chunk, end="", flush=True)
