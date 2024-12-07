from .webscout_search import WEBS
from .webscout_search_async import AsyncWEBS
from .version import __version__
from .DWEBS import *
from .tempid import *
from .LLM import VLM, LLM
from .Provider import *
from .Provider.TTI import *
from .Provider.TTS import *
from .Extra import *
from .Litlogger import *
from .optimizers import *
from .litprinter import *
from .swiftcli import *
from .litagent import LitAgent
from .scout import *
from .zeroart import *
from .zerodir import *
agent = LitAgent()

__repo__ = "https://github.com/OE-LUCIFER/Webscout"

import logging
logging.getLogger("webscout").addHandler(logging.NullHandler())
