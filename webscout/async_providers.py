from webscout import AsyncPhindSearch
from webscout import AsyncYEPCHAT
from webscout import AsyncOPENGPT
from webscout import AsyncOPENAI
from webscout import AsyncLEO
from webscout import AsyncKOBOLDAI
from webscout import AsyncGROQ
from webscout import AsyncBLACKBOXAI
from webscout.g4f import AsyncGPT4FREE

mapper: dict[str, object] = {
    "phind": AsyncPhindSearch,
    "opengpt": AsyncOPENGPT,
    "koboldai": AsyncKOBOLDAI,
    "blackboxai": AsyncBLACKBOXAI,
    "gpt4free": AsyncGPT4FREE,
    "yepchat": AsyncYEPCHAT,
    "leo": AsyncLEO,
    "groq": AsyncGROQ,
    "openai": AsyncOPENAI,
}
