import requests
import json
import re
from typing import Dict, Optional, Generator, Any
from webscout import LitAgent
from webscout import exceptions
from webscout.AIbase import AISearch


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
class Isou(AISearch):
    """A class to interact with the Isou AI search API.
    
    Isou provides a powerful search interface that returns AI-generated responses
    based on web content. It supports both streaming and non-streaming responses.
    
    Basic Usage:
        >>> from webscout import Isou
        >>> ai = Isou()
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
        {'text': 'Hello', 'links': ['http://...']}
    
    Args:
        timeout (int, optional): Request timeout in seconds. Defaults to 120.
        proxies (dict, optional): Proxy configuration for requests. Defaults to None.
    """

    def __init__(
        self,
        timeout: int = 120,
        proxies: Optional[dict] = None,
        model: str = "siliconflow:deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        logging: bool = False
    ):
        """Initialize the Isou API client.
        
        Args:
            timeout (int, optional): Request timeout in seconds. Defaults to 120.
            proxies (dict, optional): Proxy configuration for requests. Defaults to None.
            model (str, optional): Model to use for search. Defaults to DeepSeek-R1.
            logging (bool, optional): Enable logging. Defaults to False.
        """
        self.available_models = [
            "siliconflow:deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "siliconflow:Qwen/Qwen2.5-72B-Instruct-128K",
            "deepseek-reasoner"
        ]

        if model not in self.available_models:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {self.available_models}"
            )

        self.session = requests.Session()
        self.api_endpoint = "https://isou.chat/api/search"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.provider = "siliconflow" if model in self.available_models[:2] else "deepseek"
        self.mode = "simple"  # or "deep"
        self.categories = "general"  # or "science"
        self.reload = False
        
        self.headers = {
            "accept": "text/event-stream",
            "pragma": "no-cache",
            "referer": "https://isou.chat/search?q=hi",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": LitAgent().random(),
        }
        self.session.headers.update(self.headers)
        self.proxies = proxies

        # Initialize logger if enabled
        if logging:
            from webscout.Litlogger import Logger, LogFormat, ConsoleHandler
            from webscout.Litlogger.core.level import LogLevel
            
            console_handler = ConsoleHandler(
                level=LogLevel.DEBUG,
            )
            
            self.logger = Logger(
                name="Isou",                
                level=LogLevel.DEBUG,
                handlers=[console_handler]
            )
            self.logger.info("Isou initialized successfully ✨")
        else:
            self.logger = None

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """Search using the Isou API and get AI-generated responses.
        
        Args:
            prompt (str): The search query or prompt to send to the API.
            stream (bool, optional): If True, yields response chunks as they arrive.
                                   If False, returns complete response. Defaults to False.
            raw (bool, optional): If True, returns raw response dictionaries.
                                If False, returns Response objects. Defaults to False.
        
        Returns:
            Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]: 
                - If stream=False: Returns complete response
                - If stream=True: Yields response chunks as they arrive
        
        Raises:
            APIConnectionError: If the API request fails
        """
        self.provider = "siliconflow" if self.model in self.available_models[:2] else "deepseek"
        
        payload = {
            "categories": [self.categories],
            "engine": "SEARXNG",
            "language": "all",
            "mode": self.mode,
            "model": self.model,
            "provider": self.provider,
            "reload": self.reload,
            "stream": stream,
        }
        params = {"q": prompt}

        def for_stream() -> Generator[Dict[str, Any], None, None]:
            full_text = ""
            links = []
            try:
                with self.session.post(
                    self.api_endpoint,
                    params=params,
                    json=payload,
                    stream=True,
                    timeout=self.timeout,
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines(chunk_size=self.stream_chunk_size, decode_unicode=True):
                        if not line or not line.startswith('data:'):
                            continue
                        try:
                            data = json.loads(line[5:].strip())
                            
                            # Handle nested data structure
                            if 'data' in data and isinstance(data['data'], str):
                                try:
                                    nested_data = json.loads(data['data'])
                                    data.update(nested_data)
                                except json.JSONDecodeError:
                                    pass
                            
                            # Extract content and ensure it's properly decoded
                            if 'content' in data:
                                content = data['content']
                                if isinstance(content, str):
                                    # Get only the new text (delta)
                                    delta = content[len(full_text):]
                                    full_text = content
                                    
                                    # Yield the chunk
                                    if raw:
                                        yield {"text": delta, "links": links}
                                    else:
                                        yield Response(delta)
                            
                            # Extract links
                            if 'links' in data and isinstance(data['links'], list):
                                links.extend(data['links'])
                            
                        except json.JSONDecodeError:
                            continue
                            
            except requests.exceptions.RequestException as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        def for_non_stream():
            full_response = ""
            all_links = []
            for chunk in for_stream():
                if raw:
                    yield chunk
                else:
                    full_response += str(chunk)
                    if isinstance(chunk, dict):
                        all_links.extend(chunk.get("links", []))
                        
            if not raw:
                self.last_response = Response(full_response)
                return self.last_response

        return for_stream() if stream else for_non_stream()

    @staticmethod
    def format_response(text: str, links: list) -> str:
        """Format the response text with numbered citations and link list.
        
        Args:
            text (str): The response text with citation markers
            links (list): List of reference links
        
        Returns:
            str: Formatted text with numbered citations and link list
        """
        # Clean up text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Replace citations with numbers
        link_map = {f"citation:{i}]]": f"[{i}]" for i, _ in enumerate(links, start=1)}
        for key, value in link_map.items():
            text = text.replace(key, value)
        text = text.replace("[[[", "[")
        
        # Format link list
        link_list = "\n".join([f"{i}. {link}" for i, link in enumerate(links, start=1)])
        
        return f"{text}\n\nLinks:\n{link_list}"

if __name__ == "__main__":
    from rich import print
    
    # Initialize with specific model and logging
    ai = Isou(
        model="siliconflow:deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        logging=False
    )
    
    response = ai.search(input(">>> "), stream=True, raw=False)
    for chunk in response:
        print(chunk, end="", flush=True)

