"""Webscout.

Search for anything using the Google, DuckDuckGo, phind.com. Also containes AI models, can transcribe yt videos, temporary email and phone number generation, have TTS support and webai(terminal gpt and open interpeter)
"""
# webscout/__init__.py

from .webscout_search import WEBS 
from .webscout_search_async import AsyncWEBS 
from .version import __version__
from .DWEBS import DeepWEBS 
from .transcriber import transcriber
from .voice import play_audio
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
    ChatGPTlogin,
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
    # "chatgptlogin",
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
    "cli", 
    "DeepWEBS", 
    "transcriber", 
    "play_audio",

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
    "ChatGPTlogin",
]

# Set up basic logger
import logging
logging.getLogger("webscout").addHandler(logging.NullHandler()) 