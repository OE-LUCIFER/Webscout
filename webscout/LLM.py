import requests
import base64
import json
from typing import List, Dict, Union, Generator, Optional, Any

class LLMError(Exception):
    """Custom exception for LLM API errors"""
    pass

class LLM:
    """A class for interacting with the DeepInfra LLM API."""
    
    def __init__(self, model: str, system_message: str = "You are a Helpful AI."):
        """
        Initialize the LLM client.
        
        Args:
            model: The model identifier (e.g., "meta-llama/Meta-Llama-3-70B-Instruct")
            system_message: The system message to use for the conversation
        """
        self.model = model
        self.api_url = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.conversation_history = [{"role": "system", "content": system_message}]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://deepinfra.com',
            'Pragma': 'no-cache',
            'Referer': 'https://deepinfra.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'X-Deepinfra-Source': 'web-embed',
            'accept': 'text/event-stream',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }

    def _prepare_payload(
        self, 
        messages: List[Dict[str, str]], 
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 8028,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Prepare the API request payload."""
        return {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stop': stop or [],
            'stream': stream
        }

    def chat(
        self, 
        messages: List[Dict[str, str]], 
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 8028,
        stop: Optional[List[str]] = None,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Send a chat request to the DeepInfra API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stop: Optional list of stop sequences
            
        Returns:
            Either a string response or a generator for streaming
            
        Raises:
            LLMError: If the API request fails
        """
        payload = self._prepare_payload(messages, stream, temperature, max_tokens, stop)
        
        try:
            if stream:
                return self._stream_response(payload)
            else:
                return self._send_request(payload)
        except Exception as e:
            raise LLMError(f"API request failed: {str(e)}")

    def _stream_response(self, payload: Dict[str, Any]) -> Generator[str, None, None]:
        """Stream the chat response."""
        try:
            with requests.post(self.api_url, json=payload, headers=self.headers, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        if line.strip() == b'data: [DONE]':
                            break
                        if line.startswith(b'data: '):
                            try:
                                chunk = json.loads(line.decode('utf-8').removeprefix('data: '))
                                if content := chunk.get('choices', [{}])[0].get('delta', {}).get('content'):
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except requests.RequestException as e:
            raise LLMError(f"Stream request failed: {str(e)}")

    def _send_request(self, payload: Dict[str, Any]) -> str:
        """Send a non-streaming chat request."""
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.RequestException as e:
            raise LLMError(f"Request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise LLMError(f"Invalid response format: {str(e)}")
        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON response: {str(e)}")


class VLM:
    """A class for interacting with the DeepInfra VLM (Vision Language Model) API."""
    
    def __init__(self, model: str, system_message: str = "You are a Helpful AI."):
        """
        Initialize the VLM client.
        
        Args:
            model: The model identifier
            system_message: The system message to use for the conversation
        """
        self.model = model
        self.api_url = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.conversation_history = [{"role": "system", "content": system_message}]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://deepinfra.com',
            'Pragma': 'no-cache',
            'Referer': 'https://deepinfra.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'X-Deepinfra-Source': 'web-embed',
            'accept': 'text/event-stream',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }

    def chat(
        self, 
        messages: List[Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, str]]]]]]], 
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 8028,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Send a chat request with image support to the DeepInfra API.
        
        Args:
            messages: List of message dictionaries that may include image data
            stream: Whether to stream the response
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Either a string response or a generator for streaming
            
        Raises:
            LLMError: If the API request fails
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            if stream:
                return self._stream_response(payload)
            else:
                return self._send_request(payload)
        except Exception as e:
            raise LLMError(f"VLM API request failed: {str(e)}")

    def _stream_response(self, payload: Dict[str, Any]) -> Generator[str, None, None]:
        """Stream the VLM chat response."""
        try:
            with requests.post(self.api_url, json=payload, headers=self.headers, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        if line.strip() == b'data: [DONE]':
                            break
                        if line.startswith(b'data: '):
                            try:
                                chunk = json.loads(line.decode('utf-8').removeprefix('data: '))
                                if content := chunk.get('choices', [{}])[0].get('delta', {}).get('content'):
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except requests.RequestException as e:
            raise LLMError(f"VLM stream request failed: {str(e)}")

    def _send_request(self, payload: Dict[str, Any]) -> str:
        """Send a non-streaming VLM chat request."""
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.RequestException as e:
            raise LLMError(f"VLM request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise LLMError(f"Invalid VLM response format: {str(e)}")
        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid VLM JSON response: {str(e)}")


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image
        
    Raises:
        IOError: If the image file cannot be read
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except IOError as e:
        raise LLMError(f"Failed to read image file: {str(e)}")


if __name__ == "__main__":
    # Example usage
    try:
        # Initialize LLM with Llama 3 model
        llm = LLM(model="Qwen/Qwen2.5-Coder-32B-Instruct")
        
        # Example messages
        messages = [
            {"role": "user", "content": "Write a short poem about AI."}
        ]
        
        # Example 1: Non-streaming response
        print("\nNon-streaming response:")
        response = llm.chat(messages, stream=False)
        print(response)
        
        # Example 2: Streaming response
        print("\nStreaming response:")
        for chunk in llm.chat(messages, stream=True):
            print(chunk, end='', flush=True)
        print("\n")
        
    except LLMError as e:
        print(f"Error: {str(e)}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
