# webscout/Localai/__init__.py

# Import everything from the submodules
from .formats import * 
from .samplers import *
from .utils import *
from .model import *
from .thread import *

# Define what symbols are exported when using 'from webscout.Localai import *'
__all__ = [
    # From formats.py
    "blank",
    "alpaca",
    "mistral_instruct",
    "mistral_instruct_safe",
    "chatml",
    "llama2chat",
    "llama3",
    "phi3", 
    "vicuna_lmsys",
    "vicuna_common",
    "guanaco",
    "orca_mini",
    "zephyr",
    "openchat",
    "synthia",
    "neural_chat",
    "chatml_alpaca",
    "autocorrect",
    "bagel",
    "solar_instruct",
    "noromaid",
    "nschatml",
    "natural",
    "command",
    "mistral_openorca",
    "dolphin",
    "samantha",
    "jackalope",
    "naberius", 
    "hermes",
    "monad",
    "orca",
    "hexoteric", 
    "orcamaid",
    "cat",
    "mytho_cat",
    "airoboros",
    "tess", 
    "alpaca_strict",
    "wrap", # Function from formats.py

    # From samplers.py
    "SamplerSettings", 
    "GreedyDecoding",
    "DefaultSampling",
    "SimpleSampling",
    "ClassicSampling",
    "SemiSampling",
    "TikTokenSampling",
    "LowMinPSampling",
    "MinPSampling", 
    "StrictMinPSampling",
    "ContrastiveSearch",
    "WarmContrastiveSearch",
    "RandomSampling",
    "LowTempSampling", 
    "HighTempSampling",
    "MAX_TEMP", 

    # From utils.py 
    "GGUFReader",
    "softmax", 
    "cls",
    "get_timestamp_prefix_str",
    "truncate",
    "print_verbose",
    "print_info", 
    "print_warning",
    "_ArrayLike", 
    "_SupportsWriteAndFlush",
    "RESET_ALL",
    "USER_STYLE",
    "BOT_STYLE",
    "DIM_STYLE",
    "SPECIAL_STYLE",

    # From model.py and thread.py
    "Model", 
    "Thread", 
    "ModelUnloadedException",
    "assert_model_is_loaded" 
]