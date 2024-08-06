# webscout/providers/__init__.py

from .ThinkAnyAI import ThinkAnyAI
from .Xjai import Xjai
from .Llama import LLAMA
from .Cohere import Cohere
from .Reka import REKA
from .Groq import GROQ
from .Groq import AsyncGROQ
from .Openai import OPENAI
from .Openai import AsyncOPENAI
from .Leo import LEO
from .Leo import AsyncLEO
from .Koboldai import KOBOLDAI
from .Koboldai import AsyncKOBOLDAI
from .OpenGPT import OPENGPT
from .OpenGPT import OPENGPTv2
from .OpenGPT import AsyncOPENGPT
from .Perplexity import PERPLEXITY
from .Blackboxai import BLACKBOXAI 
from .Blackboxai import AsyncBLACKBOXAI
from .Phind import PhindSearch 
from .Phind import AsyncPhindSearch
from .Phind import Phindv2
from .Phind import AsyncPhindv2
from .Yepchat import YEPCHAT
from .Yepchat import AsyncYEPCHAT
from .Youchat import YouChat
from .Gemini import GEMINI
from .Berlin4h import Berlin4h
from .ChatGPTUK import ChatGPTUK
from .Poe import POE
from .BasedGPT import BasedGPT
from .Deepseek import DeepSeek
from .Deepinfra import DeepInfra, VLM, AsyncDeepInfra
from .VTLchat import VTLchat
from .Geminipro import GEMINIPRO
from .Geminiflash import GEMINIFLASH
from .OLLAMA import OLLAMA
from .FreeGemini import FreeGemini
from .Andi import AndiSearch
from .PizzaGPT import *
from .Llama3 import *
from .DARKAI import *
from .koala import *
from .RUBIKSAI import * 
from .meta import *

__all__ = [
    'ThinkAnyAI',
    'Xjai',
    'LLAMA', 
    'Cohere',
    'REKA',
    'GROQ',
    'AsyncGROQ',
    'OPENAI',
    'AsyncOPENAI',
    'LEO',
    'AsyncLEO',
    'KOBOLDAI',
    'AsyncKOBOLDAI',
    'OPENGPT', 
    'AsyncOPENGPT',
    'PERPLEXITY',
    'BLACKBOXAI', 
    'AsyncBLACKBOXAI',
    'PhindSearch', 
    'AsyncPhindSearch',
    'YEPCHAT',
    'AsyncYEPCHAT',
    'YouChat',
    'GEMINI',
    'Berlin4h',
    'ChatGPTUK',
    'POE',
    'BasedGPT',
    'DeepSeek',
    'DeepInfra',
    'VLM',
    'AsyncDeepInfra',
    'VTLchat',
    'AsyncPhindv2',
    'Phindv2',
    'OPENGPTv2',
    'GEMINIPRO',
    'GEMINIFLASH',
    'OLLAMA',
    'FreeGemini',
    'AndiSearch',
    'PIZZAGPT',
    'LLAMA3',
    'DARKAI',
    'KOALA',
    'RUBIKSAI',
    'Meta',
]