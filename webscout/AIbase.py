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
    pass

class Provider(ABC):

    @abstractmethod
    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Response:
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> str:
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def get_message(self, response: Response) -> str:
        raise NotImplementedError("Method needs to be implemented in subclass")

class AsyncProvider(ABC):

    @abstractmethod
    async def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> Response:
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
    ) -> str:
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def get_message(self, response: Response) -> str:
        raise NotImplementedError("Method needs to be implemented in subclass")

class TTSProvider(ABC):

    @abstractmethod
    def tts(self, text: str) -> ImageData:
        raise NotImplementedError("Method needs to be implemented in subclass")

class AsyncTTSProvider(ABC):

    @abstractmethod
    async def tts(self, text: str) -> AsyncImageData:
        raise NotImplementedError("Method needs to be implemented in subclass")

class ImageProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str, amount: int = 1) -> List[bytes]:
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def save(
        self, 
        response: List[bytes], 
        name: Optional[str] = None, 
        dir: Optional[Union[str, Path]] = None
    ) -> List[str]:
        raise NotImplementedError("Method needs to be implemented in subclass")

class AsyncImageProvider(ABC):

    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        amount: int = 1
    ) -> Union[AsyncGenerator[bytes, None], List[bytes]]:
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def save(
        self,
        response: Union[AsyncGenerator[bytes, None], List[bytes]],
        name: Optional[str] = None,
        dir: Optional[Union[str, Path]] = None
    ) -> List[str]:
        raise NotImplementedError("Method needs to be implemented in subclass")