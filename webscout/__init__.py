from .webscout_search import WEBS
from .webscout_search_async import AsyncWEBS
from .version import __version__
from .DWEBS import *
from .transcriber import transcriber
from .voice import play_audio
from .websx_search import WEBSX
from .LLM import VLM, LLM
from .YTdownloader import *
from .Bing_search import *
import g4f
from .YTdownloader import *
from .Provider import *
from .Provider.TTI import *
from .Provider.TTS import *
from .Extra import gguf
from .Extra import autollama
from .Extra import weather_ascii, weather
from .Agents import *
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
   "basedgpt",
   "deepseek",
   "deepinfra",
   "vtlchat",
   "geminiflash",
   "geminipro",
   "ollama",
   "andi",
   "llama3"
]

gpt4free_providers = [
   provider.__name__ for provider in g4f.Provider.__providers__  # if provider.working
]

available_providers = webai + gpt4free_providers


import logging
logging.getLogger("webscout").addHandler(logging.NullHandler())
