from webscout.AI import AsyncPhindSearch
from webscout.AI import AsyncYEPCHAT
from webscout.AI import AsyncOPENGPT
from webscout.AI import AsyncOPENAI
from webscout.AI import AsyncLLAMA2
from webscout.AI import AsyncLEO
from webscout.AI import AsyncKOBOLDAI
from webscout.AI import AsyncGROQ
from webscout.AI import AsyncBLACKBOXAI
from webscout.g4f import AsyncGPT4FREE

mapper: dict[str, object] = {
    "phind": AsyncPhindSearch,
    "opengpt": AsyncOPENGPT,
    "koboldai": AsyncKOBOLDAI,
    "blackboxai": AsyncBLACKBOXAI,
    "gpt4free": AsyncGPT4FREE,
    "llama2": AsyncLLAMA2,
    "yepchat": AsyncYEPCHAT,
    "leo": AsyncLEO,
    "groq": AsyncGROQ,
    "openai": AsyncOPENAI,
}
