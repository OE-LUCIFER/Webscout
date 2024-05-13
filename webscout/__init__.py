"""Webscout.

Search for anything using the Google, DuckDuckGo, phind.com. Also contains AI models, can transcribe yt videos, temporary email and phone number generation, has TTS support, and webai (terminal gpt and open interpreter).
"""
# webscout/__init__.py

from .webscout_search import WEBS
from .webscout_search_async import AsyncWEBS
from .version import __version__
from .DWEBS import DeepWEBS
from .transcriber import transcriber
from .voice import play_audio, talk
from .tempid import Client as TempMailClient, TemporaryPhoneNumber
from .models import MapsResult
from .LLM import LLM
from .Local import *
import g4f
# Import provider classes for direct access
from .Provider import (
    ThinkAnyAI,
    Xjai,
    LLAMA2,
    AsyncLLAMA2,
    Cohere,
    REKA,
    GROQ,
    AsyncGROQ,
    OPENAI,
    AsyncOPENAI,
    LEO,
    AsyncLEO,
    KOBOLDAI,
    AsyncKOBOLDAI,
    OPENGPT,
    AsyncOPENGPT,
    PERPLEXITY,
    BLACKBOXAI,
    AsyncBLACKBOXAI,
    PhindSearch,
    AsyncPhindSearch,
    YEPCHAT,
    AsyncYEPCHAT,
    YouChat,
    GEMINI,
    Berlin4h,
    ChatGPTUK,
)

__repo__ = "https://github.com/OE-LUCIFER/Webscout"

webai = [
    "leo",
    "openai",
    "opengpt",
    "koboldai",
    "gemini",
    "phind",
    "blackboxai",
    "g4fauto",
    "perplexity",
    "groq",
    "reka",
    "cohere",
    "yepchat",
    "you",
    "xjai",
    "thinkany",
    "berlin4h",
    "chatgptuk",
    "auto",
]

gpt4free_providers = [
    provider.__name__ for provider in g4f.Provider.__providers__  # if provider.working
]

available_providers = webai + gpt4free_providers

# Add all the provider classes you want to directly import to __all__
__all__ = [
    "WEBS",
    "AsyncWEBS",
    "__version__",
    "DeepWEBS",
    "transcriber",
    "play_audio",
    "talk",
    "TempMailClient", 
    "TemporaryPhoneNumber",
    "MapsResult",
    "LLM",
    "Model",
    "Thread",

    # AI Providers
    "ThinkAnyAI",
    "Xjai",
    "LLAMA2",
    "AsyncLLAMA2",
    "Cohere",
    "REKA",
    "GROQ",
    "AsyncGROQ",
    "OPENAI",
    "AsyncOPENAI",
    "LEO",
    "AsyncLEO",
    "KOBOLDAI",
    "AsyncKOBOLDAI",
    "OPENGPT",
    "AsyncOPENGPT",
    "PERPLEXITY",
    "BLACKBOXAI",
    "AsyncBLACKBOXAI",
    "PhindSearch",
    "AsyncPhindSearch",
    "YEPCHAT",
    "AsyncYEPCHAT",
    "YouChat",
    "GEMINI",
    "Berlin4h",
    "ChatGPTUK",
]

# Set up basic logger
import logging
logging.getLogger("webscout").addHandler(logging.NullHandler()) 