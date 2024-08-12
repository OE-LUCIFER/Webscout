# webscout/providers/__init__.py

from .ThinkAnyAI import ThinkAnyAI

from .Llama import LLAMA
from .Cohere import Cohere
from .Reka import REKA
from .Groq import GROQ
from .Groq import AsyncGROQ
from .Openai import OPENAI
from .Openai import AsyncOPENAI
from .Koboldai import KOBOLDAI
from .Koboldai import AsyncKOBOLDAI
from .Perplexity import *
from .Blackboxai import BLACKBOXAI 
from .Blackboxai import AsyncBLACKBOXAI
from .Phind import PhindSearch 
from .Phind import AsyncPhindSearch
from .Phind import Phindv2
from .Phind import AsyncPhindv2
from .ai4chat import *
from .Gemini import GEMINI
from .Berlin4h import Berlin4h
from .Poe import POE
from .BasedGPT import BasedGPT
from .Deepseek import DeepSeek
from .Deepinfra import DeepInfra, VLM, AsyncDeepInfra
from .Farfalle import *
from .OLLAMA import OLLAMA
from .Andi import AndiSearch
from .PizzaGPT import *
from .Llama3 import *
from .DARKAI import *
from .koala import *
from .RUBIKSAI import * 
from .meta import *
from .liaobots import *
from .DiscordRocks import *
__all__ = [
    'ThinkAnyAI',
    'Farfalle',
    'LLAMA', 
    'Cohere',
    'REKA',
    'GROQ',
    'AsyncGROQ',
    'OPENAI',
    'AsyncOPENAI',
    'KOBOLDAI',
    'AsyncKOBOLDAI',
    'Perplexity',
    'BLACKBOXAI', 
    'AsyncBLACKBOXAI',
    'PhindSearch', 
    'AsyncPhindSearch',

    'GEMINI',
    'Berlin4h',
    'POE',
    'BasedGPT',
    'DeepSeek',
    'DeepInfra',
    'VLM',
    'AsyncDeepInfra',
    'AI4Chat',
    'AsyncPhindv2',
    'Phindv2',
    'OLLAMA',
    'AndiSearch',
    'PIZZAGPT',
    'LLAMA3',
    'DARKAI',
    'KOALA',
    'RUBIKSAI',
    'Meta',
    'LiaoBots',
    'DiscordRocks',
]