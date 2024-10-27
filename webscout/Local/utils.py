import os
import sys
import struct
from enum import IntEnum
from io import BufferedReader
from typing import Dict, Iterable, TextIO, Optional, Union, Tuple, Generator, Any

from huggingface_hub import hf_hub_download
import numpy as np

from ._version import __version__, __llama_cpp_version__


# Color codes for Thread.interact()
RESET_ALL = "\x1b[39m"
USER_STYLE = "\x1b[39m\x1b[32m"
BOT_STYLE = "\x1b[39m\x1b[36m"
DIM_STYLE = "\x1b[39m\x1b[90m"
SPECIAL_STYLE = "\x1b[39m\x1b[33m"
ERROR_STYLE = "\x1b[39m\x1b[91m"

NoneType: type = type(None)

class TypeAssertionError(Exception):
    """Raised when a type assertion fails."""
    pass

class _ArrayLike(Iterable):
    """Represents any object that can be treated as a NumPy array."""
    pass

class _SupportsWriteAndFlush(TextIO):
    """Represents a file-like object supporting write and flush operations."""
    pass

class UnreachableException(Exception):
    """Raised when code reaches a theoretically unreachable state."""

    def __init__(self):
        super().__init__(
            "Unreachable code reached. Please report this issue at: "
            "https://github.com/ddh0/easy-llama/issues/new/choose"
        )

def download_model(
    repo_id: str, 
    filename: str, 
    token: Optional[str] = None, 
    cache_dir: str = ".cache",
    revision: str = "main"
) -> str:
    """
    Downloads a model file from the Hugging Face Hub.

    Args:
        repo_id (str): Hugging Face repository ID (e.g., 'facebook/bart-large-cnn')
        filename (str): Name of the file to download (e.g., 'model.bin', 'tokenizer.json')
        token (str, optional): Hugging Face API token for private repos. Defaults to None.
        cache_dir (str, optional): Local directory for storing downloaded files. 
                                 Defaults to ".cache".
        revision (str, optional): The specific model version to use. Defaults to "main".

    Returns:
        str: Path to the downloaded file.

    Raises:
        ValueError: If the repository or file is not found
        Exception: For other download-related errors
    """
    try:
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

        # Download the file
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            token=token,
            cache_dir=cache_dir,
            revision=revision,
            resume_download=True,    # Resume interrupted downloads
            force_download=False     # Use cached version if available
        )
        
        return downloaded_path

    except Exception as e:
        raise Exception(f"Error downloading model from {repo_id}: {str(e)}")

def softmax(z: _ArrayLike, T: Optional[float] = None, dtype: Optional[np.dtype] = None) -> np.ndarray:
    """
    Computes the softmax of an array-like input.

    Args:
        z (_ArrayLike): Input array.
        T (Optional[float], optional): Temperature parameter (scales input before softmax). 
                                       Defaults to None.
        dtype (Optional[np.dtype], optional): Data type for calculations. Defaults to None 
                                             (highest precision available).

    Returns:
        np.ndarray: Softmax output.
    """
    if dtype is None:
        _dtype = next(
            (getattr(np, f'float{bits}') for bits in [128, 96, 80, 64, 32, 16] 
             if hasattr(np, f'float{bits}')),
            float  # Default to Python float if no NumPy float types are available
        )
    else:
        assert_type(
            dtype,
            type,
            'dtype',
            'softmax',
            'dtype should be a floating type, such as `np.float32`'
        )
        _dtype = dtype

    _z = np.asarray(z, dtype=_dtype)
    if T is None or T == 1.0:
        exp_z = np.exp(_z - np.max(_z), dtype=_dtype)
        return exp_z / np.sum(exp_z, axis=0, dtype=_dtype)

    assert_type(T, float, "temperature value 'T'", 'softmax')

    if T == 0.0:
        result = np.zeros_like(_z, dtype=_dtype)
        result[np.argmax(_z)] = 1.0
        return result

    exp_z = np.exp(np.divide(_z, T, dtype=_dtype), dtype=_dtype)
    return exp_z / np.sum(exp_z, axis=0, dtype=_dtype)

def cls() -> None:
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')
    if os.name != 'nt':
        print("\033c\033[3J", end="", flush=True)

def truncate(text: str, max_length: int = 72) -> str:
    """Truncates a string to a given length and adds ellipsis if truncated."""
    return text if len(text) <= max_length else f"{text[:max_length - 3]}..."

def print_version_info(file: _SupportsWriteAndFlush) -> None:
    """Prints easy-llama and llama_cpp package versions."""
    print(f"webscout.Local package version: {__version__}", file=file)
    print(f"llama_cpp package version: {__llama_cpp_version__}", file=file)

def print_verbose(text: str) -> None:
    """Prints verbose messages to stderr."""
    print("webscout.Local:", text, file=sys.stderr, flush=True)

def print_info(text: str) -> None:
    """Prints informational messages to stderr."""
    print("webscout.Local: info:", text, file=sys.stderr, flush=True)

def print_warning(text: str) -> None:
    """Prints warning messages to stderr."""
    print("webscout.Local: WARNING:", text, file=sys.stderr, flush=True)

def assert_type(
    obj: object,
    expected_type: Union[type, Tuple[type, ...]],
    obj_name: str,
    code_location: str,
    hint: Optional[str] = None
) -> None:
    """
    Asserts that an object is of an expected type.

    Args:
        obj (object): The object to check.
        expected_type (Union[type, Tuple[type, ...]]): The expected type(s).
        obj_name (str): Name of the object in the code.
        code_location (str): Location of the assertion in the code.
        hint (Optional[str], optional): Additional hint for the error message.
                                        Defaults to None.

    Raises:
        TypeAssertionError: If the object is not of the expected type.
    """
    if isinstance(obj, expected_type):
        return

    if isinstance(expected_type, tuple):
        expected_types_str = ", ".join(t.__name__ for t in expected_type)
        error_msg = (
            f"{code_location}: {obj_name} should be one of "
            f"{expected_types_str}, not {type(obj).__name__}"
        )
    else:
        error_msg = (
            f"{code_location}: {obj_name} should be an instance of "
            f"{expected_type.__name__}, not {type(obj).__name__}"
        )

    if hint:
        error_msg += f" ({hint})"

    raise TypeAssertionError(error_msg)

class InferenceLock:
    """
    Context manager to prevent concurrent model inferences.

    This is primarily useful in asynchronous or multi-threaded contexts where
    concurrent calls to the model can lead to issues.
    """

    class LockFailure(Exception):
        """Raised when acquiring or releasing the lock fails."""
        pass

    def __init__(self):
        """Initializes the InferenceLock."""
        self.locked = False

    def __enter__(self):
        """Acquires the lock when entering the context."""
        return self.acquire()

    def __exit__(self, *exc_info):
        """Releases the lock when exiting the context."""
        self.release()

    async def __aenter__(self):
        """Acquires the lock asynchronously."""
        return self.__enter__()

    async def __aexit__(self, *exc_info):
        """Releases the lock asynchronously."""
        self.__exit__()

    def acquire(self):
        """Acquires the lock."""
        if self.locked:
            raise self.LockFailure("InferenceLock is already locked.")
        self.locked = True
        return self

    def release(self):
        """Releases the lock."""
        if not self.locked:
            raise self.LockFailure("InferenceLock is not acquired.")
        self.locked = False


class GGUFValueType(IntEnum):
    """
    Represents data types supported by the GGUF format.

    This enum should be kept consistent with the GGUF specification.
    """
    UINT8 = 0
    INT8 = 1
    UINT16 = 2
    INT16 = 3
    UINT32 = 4
    INT32 = 5
    FLOAT32 = 6
    BOOL = 7
    STRING = 8
    ARRAY = 9
    UINT64 = 10
    INT64 = 11
    FLOAT64 = 12


class QuickGGUFReader:
    """
    Provides methods for quickly reading metadata from GGUF files.

    Supports GGUF versions 2 and 3. Assumes little or big endian
    architecture.
    """

    SUPPORTED_GGUF_VERSIONS = [2, 3]
    VALUE_PACKING = {
        GGUFValueType.UINT8: "=B",
        GGUFValueType.INT8: "=b",
        GGUFValueType.UINT16: "=H",
        GGUFValueType.INT16: "=h",
        GGUFValueType.UINT32: "=I",
        GGUFValueType.INT32: "=i",
        GGUFValueType.FLOAT32: "=f",
        GGUFValueType.UINT64: "=Q",
        GGUFValueType.INT64: "=q",
        GGUFValueType.FLOAT64: "=d",
        GGUFValueType.BOOL: "?",
    }

    VALUE_LENGTHS = {
        GGUFValueType.UINT8: 1,
        GGUFValueType.INT8: 1,
        GGUFValueType.UINT16: 2,
        GGUFValueType.INT16: 2,
        GGUFValueType.UINT32: 4,
        GGUFValueType.INT32: 4,
        GGUFValueType.FLOAT32: 4,
        GGUFValueType.UINT64: 8,
        GGUFValueType.INT64: 8,
        GGUFValueType.FLOAT64: 8,
        GGUFValueType.BOOL: 1,
    }

    @staticmethod
    def unpack(value_type: GGUFValueType, file: BufferedReader) -> Any:
        """Unpacks a single value from the file based on its type."""
        return struct.unpack(
            QuickGGUFReader.VALUE_PACKING.get(value_type),
            file.read(QuickGGUFReader.VALUE_LENGTHS.get(value_type))
        )[0]

    @staticmethod
    def get_single(
        value_type: GGUFValueType,
        file: BufferedReader
    ) -> Union[str, int, float, bool]:
        """Reads a single value from the file."""
        if value_type == GGUFValueType.STRING:
            string_length = QuickGGUFReader.unpack(GGUFValueType.UINT64, file)
            return file.read(string_length).decode("utf-8")
        return QuickGGUFReader.unpack(value_type, file)

    @staticmethod
    def load_metadata(
        fn: os.PathLike[str] | str
    ) -> Dict[str, Union[str, int, float, bool, list]]:
        """
        Loads metadata from a GGUF file.

        Args:
            fn (Union[os.PathLike[str], str]): Path to the GGUF file.

        Returns:
            Dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the metadata.
        """

        metadata: Dict[str, Union[str, int, float, bool, list]] = {}
        with open(fn, "rb") as file:
            magic = file.read(4)
            if magic != b'GGUF':
                raise ValueError(
                    f"Invalid GGUF file (magic number mismatch: got {magic}, "
                    "expected b'GGUF')"
                )

            version = QuickGGUFReader.unpack(GGUFValueType.UINT32, file=file)
            if version not in QuickGGUFReader.SUPPORTED_GGUF_VERSIONS:
                raise ValueError(
                    f"Unsupported GGUF version: {version}. Supported versions are: "
                    f"{QuickGGUFReader.SUPPORTED_GGUF_VERSIONS}"
                )

            QuickGGUFReader.unpack(GGUFValueType.UINT64, file=file)  # tensor_count, not needed
            metadata_kv_count = QuickGGUFReader.unpack(
                GGUFValueType.UINT64 if version == 3 else GGUFValueType.UINT32, file
            )

            for _ in range(metadata_kv_count):
                if version == 3:
                    key_length = QuickGGUFReader.unpack(GGUFValueType.UINT64, file=file)
                elif version == 2:
                    key_length = 0
                    while key_length == 0:
                        key_length = QuickGGUFReader.unpack(GGUFValueType.UINT32, file=file)
                    file.read(4)  # 4 byte offset for GGUFv2

                key = file.read(key_length).decode()
                value_type = GGUFValueType(QuickGGUFReader.unpack(GGUFValueType.UINT32, file))

                if value_type == GGUFValueType.ARRAY:
                    array_value_type = GGUFValueType(QuickGGUFReader.unpack(GGUFValueType.UINT32, file))
                    array_length = QuickGGUFReader.unpack(
                        GGUFValueType.UINT64 if version == 3 else GGUFValueType.UINT32, file
                    )
                    if version == 2:
                        file.read(4)  # 4 byte offset for GGUFv2

                    metadata[key] = [
                        QuickGGUFReader.get_single(array_value_type, file) for _ in range(array_length)
                    ]
                else:
                    metadata[key] = QuickGGUFReader.get_single(value_type, file)

        return metadata