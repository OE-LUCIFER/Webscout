from typing import Optional
from sys import maxsize

from .utils import assert_type, NoneType

MAX_TEMP = float(maxsize)


class SamplerSettings:
    """
    Specifies sampling parameters for controlling text generation.

    This class allows you to fine-tune the behavior of text generation
    models by adjusting various sampling parameters. These settings are
    passed as an optional parameter to functions like `Thread.__init__()`,
    `Model.generate()`, `Model.stream()`, and `Model.stream_print()`.

    If a parameter is unspecified, the default value from llama.cpp is used.
    If all parameters are unspecified, the behavior is equivalent to
    `DefaultSampling`.

    Setting a parameter explicitly to `None` disables it. When all samplers
    are disabled, it's equivalent to `NoSampling` (unmodified probability
    distribution).

    Attributes:
        max_len_tokens (Optional[int]): Maximum number of tokens to generate.
                                       Defaults to -1 (no limit).
        top_k (Optional[int]): Number of highest probability tokens to consider.
                              Defaults to 40. Set to `None` to disable.
        top_p (Optional[float]): Nucleus sampling threshold (0.0 - 1.0).
                               Defaults to 0.95. Set to `None` to disable.
        min_p (Optional[float]): Minimum probability threshold (0.0 - 1.0).
                               Defaults to 0.05. Set to `None` to disable.
        temp (Optional[float]): Temperature for sampling (0.0 - inf).
                             Defaults to 0.8. Set to `None` to disable.
        frequency_penalty (Optional[float]): Penalty for repeating tokens.
                                            Defaults to 0.0.
        presence_penalty (Optional[float]): Penalty for generating new tokens.
                                           Defaults to 0.0.
        repeat_penalty (Optional[float]): Penalty for repeating token sequences.
                                         Defaults to 1.0.

    Presets:
        - `GreedyDecoding`: Always chooses the most likely token.
        - `DefaultSampling`: Uses default parameters from llama.cpp.
        - `NoSampling`: Unmodified probability distribution (all parameters disabled).
        - `ClassicSampling`: Reflects old llama.cpp defaults.
        - `SemiSampling`: Halfway between DefaultSampling and SimpleSampling.
        - `TikTokenSampling`: For models with large vocabularies.
        - `LowMinPSampling`, `MinPSampling`, `StrictMinPSampling`: Use `min_p` as the only active sampler.
        - `ContrastiveSearch`, `WarmContrastiveSearch`: Implement contrastive search.
        - `RandomSampling`: Outputs completely random tokens (useless).
        - `LowTempSampling`: Default sampling with reduced temperature.
        - `HighTempSampling`: Default sampling with increased temperature.
        - `LowTopPSampling`, `TopPSampling`, `StrictTopPSampling`: Use `top_p` as the primary sampler.
        - `MidnightMiqu`: For sophosympatheia/Midnight-Miqu-70B-v1.5 model.
        - `Llama3`: For meta-llama/Meta-Llama-3.1-8B-Instruct model.
        - `Nemo`: For mistralai/Mistral-Nemo-Instruct-2407 model.
    """

    param_types: dict[str, tuple[type]] = {
        "max_len_tokens": (int, NoneType),
        "top_k": (int, NoneType),
        "top_p": (float, NoneType),
        "min_p": (float, NoneType),
        "temp": (float, NoneType),
        "frequency_penalty": (float, NoneType),
        "presence_penalty": (float, NoneType),
        "repeat_penalty": (float, NoneType),
    }

    def __init__(
        self,
        max_len_tokens: Optional[int] = -1,
        top_k: Optional[int] = 40,
        top_p: Optional[float] = 0.95,
        min_p: Optional[float] = 0.05,
        temp: Optional[float] = 0.8,
        frequency_penalty: Optional[float] = 0.0,
        presence_penalty: Optional[float] = 0.0,
        repeat_penalty: Optional[float] = 1.0,
    ):
        self.max_len_tokens = max_len_tokens if max_len_tokens is not None else -1
        self.top_k = top_k if top_k is not None else -1
        self.top_p = top_p if top_p is not None else 1.0
        self.min_p = min_p if min_p is not None else 0.0
        self.temp = temp if temp is not None else 1.0
        self.frequency_penalty = (
            frequency_penalty if frequency_penalty is not None else 0.0
        )
        self.presence_penalty = (
            presence_penalty if presence_penalty is not None else 0.0
        )
        self.repeat_penalty = repeat_penalty if repeat_penalty is not None else 1.0

        # Validate parameters using param_types dictionary
        for param_name, param_value in self.__dict__.items():
            assert_type(
                param_value,
                self.param_types[param_name],
                f"{param_name} parameter",
                "SamplerSettings",
            )

    def __repr__(self) -> str:
        params = ", ".join(f"{name}={value}" for name, value in self.__dict__.items())
        return f"SamplerSettings({params})"


# Predefined sampler settings
GreedyDecoding = SamplerSettings(temp=0.0)
DefaultSampling = SamplerSettings()
NoSampling = SimpleSampling = SamplerSettings(
    top_k=None, top_p=None, min_p=None, temp=None
)
ClassicSampling = SamplerSettings(min_p=None, repeat_penalty=1.1)
SemiSampling = SamplerSettings(top_k=80, top_p=0.975, min_p=0.025, temp=0.9)
TikTokenSampling = SamplerSettings(temp=0.65)
LowMinPSampling = SamplerSettings(top_k=None, top_p=None, min_p=0.01, temp=None)
MinPSampling = SamplerSettings(top_k=None, top_p=None, min_p=0.075, temp=None)
StrictMinPSampling = SamplerSettings(top_k=None, top_p=None, min_p=0.2, temp=None)
ContrastiveSearch = SamplerSettings(
    top_k=None, top_p=None, min_p=None, temp=0.0, presence_penalty=0.6
)
WarmContrastiveSearch = SamplerSettings(
    top_k=None, top_p=None, min_p=None, temp=0.0, presence_penalty=1.0
)
RandomSampling = SamplerSettings(top_k=None, top_p=None, min_p=None, temp=MAX_TEMP)
LowTempSampling = SamplerSettings(temp=0.4)
HighTempSampling = SamplerSettings(temp=1.1)
LowTopPSampling = SamplerSettings(top_k=None, top_p=0.98, min_p=None, temp=None)
TopPSampling = SamplerSettings(top_k=None, top_p=0.9, min_p=None, temp=None)
StrictTopPSampling = SamplerSettings(top_k=None, top_p=0.7, min_p=None, temp=None)

# Model-specific samplers
MidnightMiqu = SamplerSettings(
    top_k=None, top_p=None, min_p=0.12, temp=1.0, repeat_penalty=1.05
)  # sophosympatheia/Midnight-Miqu-70B-v1.5
Llama3 = SamplerSettings(
    top_k=None, top_p=0.9, min_p=None, temp=0.6
)  # meta-llama/Meta-Llama-3.1-8B-Instruct
Nemo = MistralNemo = MistralSmall = SamplerSettings(
    top_k=None, top_p=0.85, min_p=None, temp=0.7
)  # mistralai/Mistral-Nemo-Instruct-2407
