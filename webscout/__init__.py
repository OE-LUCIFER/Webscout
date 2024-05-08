"""Webscout.

Search for anything using the Google, DuckDuckGo, phind.com. Also containes AI models, can transcribe yt videos, temporary email and phone number generation, have TTS support and webai(terminal gpt and open interpeter)
"""
import g4f
import logging
from .webscout_search import WEBS
from .webscout_search_async import AsyncWEBS
from .version import __version__
from .DWEBS import DeepWEBS
from .transcriber import transcriber
from .voice import play_audio


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
    "xjai"
]

gpt4free_providers = [
    provider.__name__ for provider in g4f.Provider.__providers__  # if provider.working
]

available_providers = webai + gpt4free_providers

__all__ = ["WEBS", "AsyncWEBS", "__version__", "cli"]

logging.getLogger("webscout").addHandler(logging.NullHandler())
