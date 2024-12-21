# webscout/providers/__init__.py
from .PI import *
from .Llama import LLAMA
from .Cohere import Cohere
from .Reka import REKA
from .Groq import GROQ
from .Groq import AsyncGROQ
from .Openai import OPENAI
from .Openai import AsyncOPENAI
from .Koboldai import KOBOLDAI
from .Koboldai import AsyncKOBOLDAI
from .Blackboxai import BLACKBOXAI 
from .Phind import PhindSearch 
from .Phind import Phindv2
from .ai4chat import *
from .Gemini import GEMINI
from .Deepseek import DeepSeek
from .Deepinfra import DeepInfra
from .Farfalle import *
from .cleeai import *
from .OLLAMA import OLLAMA
from .Andi import AndiSearch
from .PizzaGPT import *
from .Llama3 import *
from .DARKAI import *
from .koala import *
from .RUBIKSAI import * 
from .meta import *
from .DiscordRocks import *
from .julius import *
from .Youchat import *
from .yep import *
from .Cloudflare import *
from .turboseek import *
from .Free2GPT import *
from .EDITEE import *
from .TeachAnything import *
from .AI21 import *
from .Chatify import *
from .x0gpt import *
from .cerebras import *
from .lepton import *
from .geminiapi import *
from .elmo import *
from .Bing import *
from .GPTWeb import *
from .Netwrck import Netwrck
from .llamatutor import *
from .promptrefine import *
from .tutorai import *
from .ChatGPTES import *
from .Amigo import *
from .bagoodex import *
from .aimathgpt import *
from .gaurish import *
from .geminiprorealtime import *
from .NinjaChat import *
from .llmchat import *
from .talkai import *
from .askmyai import *
from .llama3mitril import *
from .Marcus import *
from .typegpt import *
from .mhystical import *
from .multichat import *
from .Jadve import *
__all__ = [
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
    'BLACKBOXAI', 
    'PhindSearch', 
    'GEMINI',
    'DeepSeek',
    'DeepInfra',
    'AI4Chat',
    'Phindv2',
    'OLLAMA',
    'AndiSearch',
    'PIZZAGPT',
    'LLAMA3',
    'DARKAI',
    'KOALA',
    'RUBIKSAI',
    'Meta',
    'AskMyAI',
    'DiscordRocks',
    'PiAI',
    'Julius',
    'YouChat',
    'YEPCHAT',
    'Cloudflare',
    'TurboSeek',
    'Editee',
    'TeachAnything',
    'AI21',
    'Chatify',
    'X0GPT',
    'Cerebras',
    'Lepton',
    'GEMINIAPI',
    'Cleeai',
    'Elmo',
    'Free2GPT',
    'Bing',
    'GPTWeb',
    'Netwrck',
    'LlamaTutor',
    'PromptRefine',
    'TutorAI',
    'ChatGPTES',
    'AmigoChat',
    'Bagoodex',
    'AIMathGPT',
    'GaurishCerebras',
    'GeminiPro',
    'NinjaChat',
    'LLMChat',
    'Talkai',
    'Llama3Mitril',
    'Marcus',
    'TypeGPT',
    'Mhystical',
    'Netwrck',
    'MultiChatAI',
    'JadveOpenAI',
]
