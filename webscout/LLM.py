"""
>>> from webscout.LLM import LLM, VLM
>>> llm = LLM("meta-llama/Meta-Llama-3-70B-Instruct")
>>> response = llm.chat([{"role": "user", "content": "What's good?"}])
>>> print(response)
'Hey! I'm doing great, thanks for asking! How can I help you today? 😊'

>>> # For vision tasks
>>> vlm = VLM("cogvlm-grounding-generalist")
>>> response = vlm.chat([{"role": "user", "content": [{"type": "image", "image_url": "path/to/image.jpg"}, {"type": "text", "text": "What's in this image?"}]}])
"""

import requests
import base64
import json
from typing import List, Dict, Union, Generator, Optional, Any

class LLMError(Exception):
    """Custom exception for LLM API errors 🚫

    Examples:
        >>> try:
        ...     raise LLMError("API key not found!")
        ... except LLMError as e:
        ...     print(f"Error: {e}")
        Error: API key not found!
    """
    pass

class LLM:
    """A class for chatting with DeepInfra's powerful language models! 🚀

    This class lets you:
    - Chat with state-of-the-art language models 💬
    - Stream responses in real-time ⚡
    - Control temperature and token limits 🎮
    - Handle system messages and chat history 📝

    Examples:
        >>> from webscout.LLM import LLM
        >>> llm = LLM("meta-llama/Meta-Llama-3-70B-Instruct")
        >>> response = llm.chat([
        ...     {"role": "user", "content": "Write a short poem!"}
        ... ])
        >>> print(response)
        'Through starlit skies and morning dew,
        Nature's beauty, forever new.
        In every moment, magic gleams,
        Life's poetry flows like gentle streams.'
    """
    
    def __init__(self, model: str, system_message: str = "You are a Helpful AI."):
        """
        Initialize the LLM client.
        
        Args:
            model: The model identifier (e.g., "meta-llama/Meta-Llama-3-70B-Instruct")
            system_message: The system message to use for the conversation
            
        Examples:
            >>> llm = LLM("meta-llama/Meta-Llama-3-70B-Instruct")
            >>> print(llm.model)
            'meta-llama/Meta-Llama-3-70B-Instruct'
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
        """Prepare the chat payload with all the right settings! 🎯

        Args:
            messages: Your chat messages (role & content)
            stream: Want real-time responses? Set True! ⚡
            temperature: Creativity level (0-1) 🎨
            max_tokens: Max words to generate 📝
            stop: Words to stop at (optional) 🛑

        Returns:
            Dict with all the API settings ready to go! 🚀

        Examples:
            >>> llm = LLM("meta-llama/Meta-Llama-3-70B-Instruct")
            >>> payload = llm._prepare_payload([
            ...     {"role": "user", "content": "Hi!"}
            ... ])
            >>> print(payload['model'])
            'meta-llama/Meta-Llama-3-70B-Instruct'
        """
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
        """Start chatting with the AI! 💬

        This method is your gateway to:
        - Having awesome conversations 🗣️
        - Getting creative responses 🎨
        - Streaming real-time replies ⚡
        - Controlling the output style 🎮

        Args:
            messages: Your chat messages (role & content)
            stream: Want real-time responses? Set True!
            temperature: Creativity level (0-1)
            max_tokens: Max words to generate
            stop: Words to stop at (optional)

        Returns:
            Either a complete response or streaming generator

        Raises:
            LLMError: If something goes wrong 🚫

        Examples:
            >>> llm = LLM("meta-llama/Meta-Llama-3-70B-Instruct")
            >>> # Regular chat
            >>> response = llm.chat([
            ...     {"role": "user", "content": "Tell me a joke!"}
            ... ])
            >>> # Streaming chat
            >>> for chunk in llm.chat([
            ...     {"role": "user", "content": "Tell me a story!"}
            ... ], stream=True):
            ...     print(chunk, end='')
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
        """Stream the chat response in real-time! ⚡

        Args:
            payload: The prepared chat payload

        Yields:
            Streaming chunks of the response

        Raises:
            LLMError: If the stream request fails 🚫

        Examples:
            >>> llm = LLM("meta-llama/Meta-Llama-3-70B-Instruct")
            >>> for chunk in llm._stream_response(llm._prepare_payload([
            ...     {"role": "user", "content": "Tell me a story!"}
            ... ])):
            ...     print(chunk, end='')
        """
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
        """Send a non-streaming chat request.

        Args:
            payload: The prepared chat payload

        Returns:
            The complete response

        Raises:
            LLMError: If the request fails 🚫

        Examples:
            >>> llm = LLM("meta-llama/Meta-Llama-3-70B-Instruct")
            >>> response = llm._send_request(llm._prepare_payload([
            ...     {"role": "user", "content": "Tell me a joke!"}
            ... ]))
            >>> print(response)
        """
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
    """Your gateway to vision-language AI magic! 🖼️

    This class lets you:
    - Chat about images with AI 🎨
    - Get detailed image descriptions 📝
    - Answer questions about images 🤔
    - Stream responses in real-time ⚡

    Examples:
        >>> from webscout.LLM import VLM
        >>> vlm = VLM("cogvlm-grounding-generalist")
        >>> # Chat about an image
        >>> response = vlm.chat([{
        ...     "role": "user",
        ...     "content": [
        ...         {"type": "image", "image_url": "path/to/image.jpg"},
        ...         {"type": "text", "text": "What's in this image?"}
        ...     ]
        ... }])
        >>> print(response)
        'I see a beautiful sunset over mountains...'
    """

    def __init__(self, model: str, system_message: str = "You are a Helpful AI."):
        """Get ready for some vision-language magic! 🚀

        Args:
            model: Your chosen vision model
            system_message: Set the AI's personality

        Examples:
            >>> vlm = VLM("cogvlm-grounding-generalist")
            >>> print(vlm.model)
            'cogvlm-grounding-generalist'
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
        """Chat about images with AI! 🖼️

        This method lets you:
        - Ask questions about images 🤔
        - Get detailed descriptions 📝
        - Stream responses in real-time ⚡
        - Control response creativity 🎨

        Args:
            messages: Your chat + image data
            stream: Want real-time responses?
            temperature: Creativity level (0-1)
            max_tokens: Max words to generate

        Returns:
            Either a complete response or streaming generator

        Raises:
            LLMError: If something goes wrong 🚫

        Examples:
            >>> vlm = VLM("cogvlm-grounding-generalist")
            >>> # Regular chat with image
            >>> response = vlm.chat([{
            ...     "role": "user",
            ...     "content": [
            ...         {"type": "image", "image_url": "sunset.jpg"},
            ...         {"type": "text", "text": "Describe this scene"}
            ...     ]
            ... }])
            >>> # Streaming chat
            >>> for chunk in vlm.chat([...], stream=True):
            ...     print(chunk, end='')
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
    """Turn your image into base64 magic! 🎨

    Args:
        image_path: Where's your image at?

    Returns:
        Your image as a base64 string ✨

    Raises:
        IOError: If we can't read your image 🚫

    Examples:
        >>> from webscout.LLM import encode_image_to_base64
        >>> image_data = encode_image_to_base64("cool_pic.jpg")
        >>> print(len(image_data))  # Check the encoded length
        12345
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
