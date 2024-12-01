from .webscout_search import WEBS
from .webscout_search_async import AsyncWEBS
from .version import __version__
from .DWEBS import *
from .transcriber import *
from .requestsHTMLfix import *
from .tempid import *
from .LLM import VLM, LLM
from .YTdownloader import *
from .Bing_search import *
from .YTdownloader import *
from .Provider import *
from .Provider.TTI import *
from .Provider.TTS import *
from .Extra import *
from .Litlogger import *
from .Agents import *
from .optimizers import *
from .litprinter import *
from .swiftcli import *
from .litagent import *

__repo__ = "https://github.com/OE-LUCIFER/Webscout"

import logging
logging.getLogger("webscout").addHandler(logging.NullHandler())
