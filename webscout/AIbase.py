from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import AsyncGenerator, List, Union, Generator, Optional
from typing_extensions import TypeAlias

# Type aliases for better readability
Response: TypeAlias = dict[str, Union[str, bool, None]]
ImageData: TypeAlias = Union[bytes, str, Generator[bytes, None, None]]
AsyncImageData: TypeAlias = Union[bytes, str, AsyncGenerator[bytes, None]]

class AIProviderError(Exception):
    """Base exception for AI provider errors"""
    pass

class Provider(ABC):
    """Base class for text-based AI providers.
    
    This class defines the interface for synchronous AI text generation providers.
    All text-based AI providers should inherit from this class and implement
    its abstract methods.
    """

    @abstractmethod
    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Response:
        """Chat with AI and get detailed response.

        Args:
            prompt: The input text to send to the AI
            stream: Whether to stream the response. Defaults to False
            raw: Whether to return raw response as received. Defaults to False
            optimizer: Optional prompt optimizer - choices: ['code', 'shell_command']
            conversationally: Whether to maintain conversation context. Defaults to False

        Returns:
            A dictionary containing response details:
            {
                "completion": str,        # The AI's response
                "stop_reason": str|None,  # Reason for response termination
                "truncated": bool,        # Whether response was truncated
                "stop": str|None,        # Stop token if any
                "model": str,            # Model used for generation
                "log_id": str,           # Unique log identifier
                "exception": str|None    # Error message if any
            }

        Raises:
            AIProviderError: If there's an error communicating with the AI provider
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> str:
        """Generate a simple text response from the AI.

        Args:
            prompt: The input text to send to the AI
            stream: Whether to stream the response. Defaults to False
            optimizer: Optional prompt optimizer - choices: ['code', 'shell_command']
            conversationally: Whether to maintain conversation context. Defaults to False

        Returns:
            The AI's text response

        Raises:
            AIProviderError: If there's an error communicating with the AI provider
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def get_message(self, response: Response) -> str:
        """Extract the message content from a response dictionary.

        Args:
            response: Response dictionary from ask() method

        Returns:
            The extracted message text

        Raises:
            AIProviderError: If message cannot be extracted from response
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

class AsyncProvider(ABC):
    """Asynchronous base class for text-based AI providers"""

    @abstractmethod
    async def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Response:
        """Asynchronously chat with AI and get detailed response.

        Args:
            prompt: The input text to send to the AI
            stream: Whether to stream the response. Defaults to False
            raw: Whether to return raw response as received. Defaults to False
            optimizer: Optional prompt optimizer - choices: ['code', 'shell_command']
            conversationally: Whether to maintain conversation context. Defaults to False

        Returns:
            A dictionary containing response details:
            {
                "completion": str,        # The AI's response
                "stop_reason": str|None,  # Reason for response termination
                "truncated": bool,        # Whether response was truncated
                "stop": str|None,        # Stop token if any
                "model": str,            # Model used for generation
                "log_id": str,           # Unique log identifier
                "exception": str|None    # Error message if any
            }

        Raises:
            AIProviderError: If there's an error communicating with the AI provider
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> str:
        """Asynchronously generate a simple text response from the AI.

        Args:
            prompt: The input text to send to the AI
            stream: Whether to stream the response. Defaults to False
            optimizer: Optional prompt optimizer - choices: ['code', 'shell_command']
            conversationally: Whether to maintain conversation context. Defaults to False

        Returns:
            The AI's text response

        Raises:
            AIProviderError: If there's an error communicating with the AI provider
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def get_message(self, response: Response) -> str:
        """Asynchronously extract the message content from a response dictionary.

        Args:
            response: Response dictionary from ask() method

        Returns:
            The extracted message text

        Raises:
            AIProviderError: If message cannot be extracted from response
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

class TTSProvider(ABC):
    """Base class for text-to-speech providers.
    
    This class defines the interface for synchronous text-to-speech providers.
    """

    @abstractmethod
    def tts(self, text: str) -> ImageData:
        """Convert text to speech.

        Args:
            text: The text to convert to speech

        Returns:
            One of:
            - Raw audio bytes
            - Path to saved audio file
            - Generator yielding audio chunks

        Raises:
            AIProviderError: If text-to-speech conversion fails
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

class AsyncTTSProvider(ABC):
    """Base class for asynchronous text-to-speech providers."""

    @abstractmethod
    async def tts(self, text: str) -> AsyncImageData:
        """Asynchronously convert text to speech.

        Args:
            text: The text to convert to speech

        Returns:
            One of:
            - Raw audio bytes
            - Path to saved audio file
            - AsyncGenerator yielding audio chunks

        Raises:
            AIProviderError: If text-to-speech conversion fails
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

class ImageProvider(ABC):
    """Base class for text-to-image generation providers."""

    @abstractmethod
    def generate(self, prompt: str, amount: int = 1) -> List[bytes]:
        """Generate images from a text description.

        Args:
            prompt: Text description of desired image
            amount: Number of images to generate (default: 1)

        Returns:
            List of generated images as bytes

        Raises:
            AIProviderError: If image generation fails
            ValueError: If amount is less than 1
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def save(
        self, 
        response: List[bytes], 
        name: Optional[str] = None, 
        dir: Optional[Union[str, Path]] = None
    ) -> List[str]:
        """Save generated images to disk.

        Args:
            response: List of image data in bytes
            name: Base filename for saved images (default: auto-generated)
            dir: Directory to save images (default: current directory)

        Returns:
            List of paths to saved image files

        Raises:
            AIProviderError: If saving images fails
            ValueError: If response is empty
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

class AsyncImageProvider(ABC):
    """Base class for asynchronous text-to-image generation providers."""

    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        amount: int = 1
    ) -> Union[AsyncGenerator[bytes, None], List[bytes]]:
        """Asynchronously generate images from text.

        Args:
            prompt: Text description of desired image
            amount: Number of images to generate (default: 1)

        Returns:
            Either:
            - AsyncGenerator yielding image bytes for streaming
            - List of image bytes if not streaming

        Raises:
            AIProviderError: If image generation fails
            ValueError: If amount is less than 1
        """
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def save(
        self,
        response: Union[AsyncGenerator[bytes, None], List[bytes]],
        name: Optional[str] = None,
        dir: Optional[Union[str, Path]] = None
    ) -> List[str]:
        """Asynchronously save generated images.

        Args:
            response: Either AsyncGenerator yielding images or List of image bytes
            name: Base filename for saved images (default: auto-generated)
            dir: Directory to save images (default: current directory)

        Returns:
            List of paths to saved image files

        Raises:
            AIProviderError: If saving images fails
            ValueError: If response is empty
        """
        raise NotImplementedError("Method needs to be implemented in subclass")