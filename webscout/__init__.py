from .webscout_search import WEBS
from .webscout_search_async import AsyncWEBS
from .version import __version__
from .DWEBS import DeepWEBS
from .transcriber import transcriber
from .voice import play_audio
# from .tempid import Client as TempMailClient, TemporaryPhoneNumber
from .LLM import LLM
# from .Local import *
import g4f
# Import provider classes for direct access
from .Provider import *

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
   "poe",
]

gpt4free_providers = [
   provider.__name__ for provider in g4f.Provider.__providers__  # if provider.working
]

available_providers = webai + gpt4free_providers

# Add all the provider classes, Localai models, Thread, and Model to __all__
__all__ = [
   "WEBS",
   "AsyncWEBS",
   "__version__",
   "DeepWEBS",
   "transcriber",
   "play_audio",
   "TempMailClient", 
   "TemporaryPhoneNumber",
   "LLM",
   # Localai models and utilities 
   # "Model",
   # "Thread",
   # "formats", 

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
   "POE"
]

import logging
logging.getLogger("webscout").addHandler(logging.NullHandler())
