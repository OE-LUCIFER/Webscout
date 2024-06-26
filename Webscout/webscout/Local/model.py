import json
from ._version import __version__, __llama_cpp_version__

"""Submodule containing the Model class to work with language models"""

import sys
import numpy as np

from .utils import (
    _SupportsWriteAndFlush,
    print_warning,
    print_verbose,
    GGUFReader,
    softmax
)

from .samplers import SamplerSettings, DefaultSampling
from llama_cpp import Llama, StoppingCriteriaList
from typing    import Callable, Generator, Optional, Union
from os.path   import isdir, exists
from heapq     import nlargest

from os import cpu_count as os_cpu_count


class ModelUnloadedException(Exception):
    """Exception raised when trying to use a Model that has been unloaded"""
    def __init__(self, message):
        self.message = message
        self.tool_code_start = "```tool_code\n"  # Define tool code markers
        self.tool_code_end = "\n```tool_code```"
        super().__init__(self.message)
        self.add_note('Are you trying to use a Model that has been unloaded?')

class Model:
    """
    A high-level abstraction of a llama model

    This is just a brief overview of webscout.Local.Model.
    To see a full description of each method and its parameters,
    call help(Model), or see the relevant docstring.

    The following methods are available:
    - `.generate()` - Generate text
    - `.get_length()` - Get the length of a given text in tokens
    - `.ingest()` - Ingest text into the model's cache
    - `.next_candidates()` - Get a list of the most likely next tokens (WIP)
    - `.stream()` - Return a Generator that can stream text as it is generated
    - `.stream_print()` - Print text as it is generated
    - `.trim()` - Trim a given text to the model's context length
    - `.unload()` - Unload the model from memory

    The following attributes are available:
    - `.bos_token` - The model's beginning-of-stream token ID
    - `.context_length` - The model's loaded context length
    - `.flash_attn` - Whether the model was loaded with `flash_attn=True`
    - `.eos_token` - The model's end-of-stream token ID
    - `.llama` - The underlying `llama_cpp.Llama` instance
    - `.metadata` - The GGUF metadata of the model
    - `.n_ctx_train` - The native context length of the model
    - `.rope_freq_base` - The model's loaded RoPE frequency base
    - `.rope_freq_base_train` - The model's native RoPE frequency base
    - `.tokens` - A list of all the tokens in the model's tokenizer
    - `.verbose` - Whether the model was loaded with `verbose=True`
    """

    def __init__(
        self,
        model_path: str,
        context_length: Optional[int] = None,
        n_gpu_layers: int = 0,
        offload_kqv: bool = True,
        flash_attn: bool = False,
        verbose: bool = False,
    ):
        """
        Given the path to a GGUF file, construct a Model instance.

        The model must be in GGUF format.

        The following parameters are optional:
        - context_length: The context length at which to load the model, in tokens
        - n_gpu_layers: The number of layers to be offloaded to the GPU
        - offload_kqv: Whether the KQV cache (context) should be offloaded
        - flash_attn: Whether to use Flash Attention
        - verbose: Whether to print additional backend information
        """

        if verbose:
            print_verbose(f"webscout.Local package version: {__version__}")
            print_verbose(f"llama_cpp package version: {__llama_cpp_version__}")

        assert isinstance(model_path, str), \
            f"Model: model_path should be a string, not {type(model_path)}"
        assert exists(model_path), \
            f"Model: the given model_path '{model_path}' does not exist"
        assert not isdir(model_path), \
            f"Model: the given model_path '{model_path}' is a directory, not a GGUF file"
        assert isinstance(context_length, (int, type(None))), \
            f"Model: context_length should be int or None, not {type(context_length)}"
        assert isinstance(flash_attn, bool), \
            f"Model: flash_attn should be bool (True or False), not {type(flash_attn)}"
        
        # save __init__ parameters for __repr__
        self._model_path = model_path
        self._context_length = context_length
        self._n_gpu_layers = n_gpu_layers
        self._offload_kqv = offload_kqv
        self._flash_attn = flash_attn
        self._verbose = self.verbose = verbose
        self.tools = {}
        # if context_length <= 0, use n_ctx_train
        if isinstance(context_length, int) and context_length <= 0:
            context_length = None

        # this does not use Llama.metadata because we want to use GGUF
        # metadata to determine some parameters of the Llama instance
        # before it is created
        self.metadata = GGUFReader.load_metadata(self, model_path)
        metadata_keys = self.metadata.keys() # only read once

        n_ctx_train = None
        for key in metadata_keys:
            if key.endswith('.context_length'):
                n_ctx_train = self.metadata[key]
                break

        if n_ctx_train is None:
            raise KeyError(
                "GGUF file does not specify a context length"
            )
        
        rope_freq_base_train = None
        for key in metadata_keys:
            if key.endswith('.rope.freq_base'):
                rope_freq_base_train = self.metadata[key]
                break

        if rope_freq_base_train is None and context_length is not None:
            if context_length > n_ctx_train:
                raise ValueError(
                    'unable to load model with greater than native ' + \
                    f'context length ({context_length} > {n_ctx_train}) ' + \
                    'because model does not specify freq_base. ' + \
                    f'try again with `context_length={n_ctx_train}`'
                )

        if rope_freq_base_train is None or context_length is None or \
            context_length <= n_ctx_train:
            # no need to do context scaling, load model normally

            if context_length is None:
                self.context_length = n_ctx_train
            else:
                self.context_length = context_length
            rope_freq_base = rope_freq_base_train

        elif context_length > n_ctx_train:
            # multiply rope_freq_base according to requested context length
            # because context length > n_ctx_train and rope freq base is known

            rope_freq_base = (context_length/n_ctx_train)*rope_freq_base_train
            self.context_length = context_length
            
            if self.verbose:
                print_verbose(
                    'chosen context length is greater than native context '
                    f'length ({context_length} > {n_ctx_train}), '
                    'rope_freq_base will be changed from '
                    f'{rope_freq_base_train} to {rope_freq_base}'
                )

            if 2 <= context_length/n_ctx_train < 4:
                print_warning(
                    'loading model with 2x native context length or more, '
                    'expect small loss of quality'
                )
            
            elif 4 <= context_length/n_ctx_train < 8:
                print_warning(
                    'loading model with 4x native context length or more, '
                    'expect moderate loss of quality'
                )

            elif context_length/n_ctx_train >= 8:
                print_warning(
                    'loading model with 8x native context length or more, '
                    'expect SIGNIFICANT loss of quality'
                )
        
        try:
            self.tokens: list[str] = self.metadata['tokenizer.ggml.tokens']
        except KeyError:
            print_warning(
                "could not set Model.tokens, defaulting to None"
            )
            self.tokens = None
        try:
            self.bos_token: int = self.metadata['tokenizer.ggml.bos_token_id']
        except KeyError:
            print_warning(
                "could not set Model.bos_token, defaulting to None"
            )
            self.bos_token = None
        try:
            self.eos_token: int = self.metadata['tokenizer.ggml.eos_token_id']
        except KeyError:
            print_warning(
                "could not set Model.eos_token, defaulting to None"
            )
            self.eos_token = None

        cpu_count = os_cpu_count()

        # these values for n_threads and n_threads_batch are
        # known to be optimal for most systems
        n_batch = 512 # can this be optimized?
        n_threads = max(cpu_count//2, 1)
        n_threads_batch = cpu_count

        if flash_attn and n_gpu_layers == 0:
            print_warning(
                "disabling flash_attn because n_gpu_layers == 0"
            )
            flash_attn = False
        
        # guard against models with no rope_freq_base
        if rope_freq_base is None:
            rope_freq_base = 0

        self.llama: Llama = Llama(
            model_path=model_path,
            n_ctx=self.context_length,
            n_gpu_layers=n_gpu_layers,
            use_mmap=True,
            use_mlock=False,
            logits_all=False,
            n_batch=n_batch,
            n_threads=n_threads,
            n_threads_batch=n_threads_batch,
            rope_freq_base=rope_freq_base,
            mul_mat_q=True,
            offload_kqv=offload_kqv,
            flash_attn=flash_attn,
            # KV cache quantization
            # use 1 for F16 (default), 8 for q8_0, 2 for q4_0, 3 for q4_1
            #type_k=8,
            #type_v=8,
            verbose=verbose
        )
        
        # once model is loaded, replace metadata (as read using internal class)
        # with metadata (as read using the more robust llama-cpp-python code) 
        self.metadata = self.llama.metadata

        # expose these values because they may be useful / informative
        self.n_ctx_train = n_ctx_train
        self.rope_freq_base_train = rope_freq_base_train
        self.rope_freq_base = rope_freq_base
        self.flash_attn = flash_attn

        if self.verbose:
            print_verbose("new Model instance with the following attributes:")
            print_verbose(f"model: {model_path}")
            print_verbose(f"param: n_gpu_layers         == {n_gpu_layers}")
            print_verbose(f"param: offload_kqv          == {offload_kqv}")
            print_verbose(f"param: flash_attn           == {flash_attn}")
            print_verbose(f"param: n_batch              == {n_batch}")
            print_verbose(f"param: n_threads            == {n_threads}")
            print_verbose(f"param: n_threads_batch      == {n_threads_batch}")
            print_verbose(f" gguf: n_ctx_train          == {n_ctx_train}")
            print_verbose(f"param: self.context_length  == {self.context_length}")
            print_verbose(f" gguf: rope_freq_base_train == {rope_freq_base_train}")
            print_verbose(f"param: rope_freq_base       == {rope_freq_base}")
    def register_tool(self, name: str, function: Callable):
        """Registers a tool for function calling."""
        self.tools[name] = function

    def _extract_tool_code(self, text: str) -> dict:
        """Extracts tool code from the model's output."""
        try:
            start = text.find(self.tool_code_start) + len(self.tool_code_start)
            end = text.find(self.tool_code_end)
            tool_code_json = text[start:end]
            tool_code = json.loads(tool_code_json)
            return tool_code
        except (ValueError, json.JSONDecodeError):
            return None
    def _should_call_tool(self, response_text: str) -> bool:
        """Determines if the model suggests a tool call."""
        # Simple check for tool code markers in response
        return self.tool_code_start in response_text and self.tool_code_end in response_text
    def generate(
        self,
        prompt: Union[str, list[int]],
        stops: list[Union[str, int]] = [],
        sampler: SamplerSettings = DefaultSampling,
        max_iterations: int = 3, # Maximum iterations for tool calls
    ) -> str:
        """
        Generates text and handles tool calls.

        Args:
            prompt (Union[str, list[int]]): The input prompt.
            stops (list[Union[str, int]]): Stop sequences.
            sampler (SamplerSettings): Sampler settings.
            max_iterations (int): Maximum number of tool call iterations. 

        Returns:
            str: The generated text.
        """
        assert_model_is_loaded(self)
        response_text = self.llama.create_completion(
            prompt,
            max_tokens=sampler.max_len_tokens,
            temperature=sampler.temp,
            top_p=sampler.top_p,
            min_p=sampler.min_p,
            frequency_penalty=sampler.frequency_penalty,
            presence_penalty=sampler.presence_penalty,
            repeat_penalty=sampler.repeat_penalty,
            top_k=sampler.top_k,
            stop=stops
        )['choices'][0]['text']

        iteration = 0
        while self._should_call_tool(response_text) and iteration < max_iterations:
            tool_code = self._extract_tool_code(response_text)
            if tool_code:
                tool_name = tool_code.get("function", {}).get("name")
                arguments = tool_code.get("function", {}).get("arguments", "")
                if tool_name and arguments and tool_name in self.tools:
                    # Execute the tool and append its output
                    tool_output = self.tools[tool_name](**json.loads(arguments))
                    response_text = response_text.replace(
                        f"{self.tool_code_start}{json.dumps(tool_code)}{self.tool_code_end}", 
                        tool_output
                    )
            iteration += 1

        return response_text
    def __repr__(self) -> str:
        return \
            f"Model({repr(self._model_path)}, " + \
            f"context_length={self._context_length}, " + \
            f"n_gpu_layers={self._n_gpu_layers}, " + \
            f"offload_kqv={self._offload_kqv}, "+ \
            f"flash_attn={self._flash_attn}, " + \
            f"verbose={self._verbose})"

    def __del__(self):
        self.unload()
    
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.unload()
    
    def __call__(
        self,
        prompt: Union[str, list[int]],
        stops: list[Union[str, int]] = [],
        sampler: SamplerSettings = DefaultSampling
    ) -> str:
        """
        `Model(...)` is a shorthand for `Model.generate(...)`
        """
        return self.generate(prompt, stops, sampler)

    def unload(self):
        """
        Unload the model from memory
        """
        # ref: llama_cpp._internals._LlamaModel.__del__()
        if not hasattr(self, 'llama'):
            # nothing can be done
            return
        try:
            if self.llama._model.model is not None:
                # actually unload the model from memory
                self.llama._model._llama_free_model(self.llama._model.model)
                self.llama._model.model = None
        except AttributeError:
            # broken or already being destroyed by GC, abort
            return
        if hasattr(self, 'llama'):
            delattr(self, 'llama')
        if self.verbose:
            print_verbose('Model unloaded')
    
    def trim(
        self,
        text: str,
        overwrite: Optional[str] = None
    ) -> str:

        """
        Trim the given text to the context length of this model,
        leaving room for two extra tokens.

        Optionally overwrite the oldest tokens with the text given in the
        `overwrite` parameter, which may be useful for keeping some
        information in context.

        Does nothing if the text is equal to or shorter than
        (context_length - 2).
        """
        assert_model_is_loaded(self)
        trim_length = self.context_length - 2
        tokens_list = self.llama.tokenize(
            text.encode("utf-8", errors="ignore")
        )

        if len(tokens_list) <= trim_length:
            if overwrite is not None:
                text[0 : len(overwrite)] = overwrite
            return text

        if len(tokens_list) > trim_length and overwrite is None:
            # cut to trim_length
            tokens_list = tokens_list[-trim_length:]
            return self.llama.detokenize(tokens_list).decode(
                "utf-8",
                errors="ignore"
            )

        if len(tokens_list) > trim_length and overwrite is not None:
            # cut to trim_length
            tokens_list = tokens_list[-trim_length:]
            overwrite_tokens = self.llama.tokenize(overwrite.encode(
                "utf-8",
                errors="ignore"
                )
            )
            # overwrite oldest tokens
            tokens_list[0 : len(overwrite_tokens)] = overwrite_tokens
            return self.llama.detokenize(tokens_list).decode(
                "utf-8",
                errors="ignore"
            )

    def get_length(self, text: str) -> int:
        """
        Return the length of the given text in tokens according to this model,
        including the appended BOS token.
        """
        assert_model_is_loaded(self)
        return len(self.llama.tokenize(
            text.encode(
                "utf-8",
                errors="ignore"
                )
            ))

    def generate(
        self,
        prompt: Union[str, list[int]],
        stops: list[Union[str, int]] = [],
        sampler: SamplerSettings = DefaultSampling
    ) -> str:
        """
        Given a prompt, return a generated string.

        prompt: The text from which to generate

        The following parameters are optional:
        - stops: A list of strings and/or token IDs at which to end the generation early
        - sampler: The SamplerSettings object used to control text generation
        """

        assert isinstance(prompt, (str, list)), \
            f"generate: prompt should be string or list[int], not {type(prompt)}"
        if isinstance(prompt, list):
            assert all(isinstance(tok, int) for tok in prompt), \
                "generate: some token in prompt is not an integer"
        assert isinstance(stops, list), \
            f"generate: parameter `stops` should be a list, not {type(stops)}"
        assert all(isinstance(item, (str, int)) for item in stops), \
            f"generate: some item in parameter `stops` is not a string or int"

        if self.verbose:
            print_verbose(f'using the following sampler settings for Model.generate:')
            print_verbose(f'max_len_tokens    == {sampler.max_len_tokens}')
            print_verbose(f'temp              == {sampler.temp}')
            print_verbose(f'top_p             == {sampler.top_p}')
            print_verbose(f'min_p             == {sampler.min_p}')
            print_verbose(f'frequency_penalty == {sampler.frequency_penalty}')
            print_verbose(f'presence_penalty  == {sampler.presence_penalty}')
            print_verbose(f'repeat_penalty    == {sampler.repeat_penalty}')
            print_verbose(f'top_k             == {sampler.top_k}')

        # if any stop item is a token ID (int)
        if any(isinstance(stop, int) for stop in stops):
            # stop_strs is a list of all stopping strings
            stop_strs: list[str] = [stop for stop in stops if isinstance(stop, str)]
            # stop_token_ids is a list of all stop token IDs
            stop_token_ids: list[int] = [tok_id for tok_id in stops if isinstance(tok_id, int)]
            def stop_on_token_ids(tokens, *args, **kwargs):
                return tokens[-1] in stop_token_ids
            stopping_criteria = StoppingCriteriaList([stop_on_token_ids])
            assert_model_is_loaded(self)
            return self.llama.create_completion(
                prompt,
                max_tokens=sampler.max_len_tokens,
                temperature=sampler.temp,
                top_p=sampler.top_p,
                min_p=sampler.min_p,
                frequency_penalty=sampler.frequency_penalty,
                presence_penalty=sampler.presence_penalty,
                repeat_penalty=sampler.repeat_penalty,
                top_k=sampler.top_k,
                stop=stop_strs,
                stopping_criteria=stopping_criteria
            )['choices'][0]['text']

        # if stop items are only strings
        assert_model_is_loaded(self)
        return self.llama.create_completion(
            prompt,
            max_tokens=sampler.max_len_tokens,
            temperature=sampler.temp,
            top_p=sampler.top_p,
            min_p=sampler.min_p,
            frequency_penalty=sampler.frequency_penalty,
            presence_penalty=sampler.presence_penalty,
            repeat_penalty=sampler.repeat_penalty,
            top_k=sampler.top_k,
            stop=stops
        )['choices'][0]['text']
    

    def stream(
        self,
        prompt: Union[str, list[int]],
        stops: list[Union[str, int]] = [],
        sampler: SamplerSettings = DefaultSampling
    ) -> Generator:

        """
        Given a prompt, return a Generator that yields dicts containing tokens.

        To get the token string itself, subscript the dict with:

        `['choices'][0]['text']`

        prompt: The text from which to generate

        The following parameters are optional:
        - stops: A list of strings and/or token IDs at which to end the generation early
        - sampler: The SamplerSettings object used to control text generation
        """

        assert isinstance(prompt, (str, list)), \
            f"stream: prompt should be string or list[int], not {type(prompt)}"
        if isinstance(prompt, list):
            assert all(isinstance(tok, int) for tok in prompt), \
                "stream: some token in prompt is not an integer"
        assert isinstance(stops, list), \
            f"stream: parameter `stops` should be a list, not {type(stops)}"
        assert all(isinstance(item, (str, int)) for item in stops), \
            f"stream: some item in parameter `stops` is not a string or int"

        if self.verbose:
            print_verbose(f'using the following sampler settings for Model.stream:')
            print_verbose(f'max_len_tokens    == {sampler.max_len_tokens}')
            print_verbose(f'temp              == {sampler.temp}')
            print_verbose(f'top_p             == {sampler.top_p}')
            print_verbose(f'min_p             == {sampler.min_p}')
            print_verbose(f'frequency_penalty == {sampler.frequency_penalty}')
            print_verbose(f'presence_penalty  == {sampler.presence_penalty}')
            print_verbose(f'repeat_penalty    == {sampler.repeat_penalty}')
            print_verbose(f'top_k             == {sampler.top_k}')
        
        # if any stop item is a token ID (int)
        if any(isinstance(stop, int) for stop in stops):
            # stop_strs is a list of all stopping strings
            stop_strs: list[str] = [stop for stop in stops if isinstance(stop, str)]
            # stop_token_ids is a list of all stop token IDs
            stop_token_ids: list[int] = [tok_id for tok_id in stops if isinstance(tok_id, int)]
            def stop_on_token_ids(tokens, *args, **kwargs):
                return tokens[-1] in stop_token_ids
            stopping_criteria = StoppingCriteriaList([stop_on_token_ids])
            assert_model_is_loaded(self)
            return self.llama.create_completion(
                prompt,
                max_tokens=sampler.max_len_tokens,
                temperature=sampler.temp,
                top_p=sampler.top_p,
                min_p=sampler.min_p,
                frequency_penalty=sampler.frequency_penalty,
                presence_penalty=sampler.presence_penalty,
                repeat_penalty=sampler.repeat_penalty,
                top_k=sampler.top_k,
                stream=True,
                stop=stop_strs,
                stopping_criteria=stopping_criteria
            )

        assert_model_is_loaded(self)
        return self.llama.create_completion(
            prompt,
            max_tokens=sampler.max_len_tokens,
            temperature=sampler.temp,
            top_p=sampler.top_p,
            min_p=sampler.min_p,
            frequency_penalty=sampler.frequency_penalty,
            presence_penalty=sampler.presence_penalty,
            repeat_penalty=sampler.repeat_penalty,
            top_k=sampler.top_k,
            stream=True,
            stop=stops
        )


    def stream_print(
        self,
        prompt: Union[str, list[int]],
        stops: list[Union[str, int]] = [],
        sampler: SamplerSettings = DefaultSampling,
        end: str = "\n",
        file: _SupportsWriteAndFlush = sys.stdout,
        flush: bool = True
    ) -> str:
        """
        Given a prompt, stream text as it is generated, and return the generated string.
        The returned string does not include the `end` parameter.

        `Model.stream_print(...)` is a shorthand for:
        
        ```
        s = Model.stream(prompt, stops=stops, sampler=sampler)
        for i in s:
            tok = i['choices'][0]['text']
            print(tok, end='', file=file, flush=flush)
        print(end, end='', file=file, flush=True)
        ```

        prompt: The text from which to generate

        The following parameters are optional:
        - stops: A list of strings and/or token IDs at which to end the generation early
        - sampler: The SamplerSettings object used to control text generation
        - end: A string to print after the generated text
        - file: The file where text should be printed
        - flush: Whether to flush the stream after each token
        """
        
        token_generator = self.stream(
            prompt=prompt,
            stops=stops,
            sampler=sampler
        )

        res = ''
        for i in token_generator:
            tok = i['choices'][0]['text']
            print(tok, end='', file=file, flush=flush)
            res += tok

        # print `end`, and always flush stream after generation is done
        print(end, end='', file=file, flush=True)

        return res


    def ingest(self, text: str) -> None:
        """
        Ingest the given text into the model's cache
        """

        assert_model_is_loaded(self)
        self.llama.create_completion(
            text,
            max_tokens=1,
            temperature=0.0
        )
    

    def candidates(
        self,
        prompt: str,
        k: int
    ) -> list[tuple[str, np.floating]]:
        """
        Given prompt `str` and k `int`, return a sorted list of the
        top k candidates for most likely next token, along with their
        normalized probabilities
        """

        assert isinstance(prompt, str), \
            f"next_candidates: prompt should be str, not {type(prompt)}"
        assert isinstance(k, int), \
            f"next_candidates: k should be int, not {type(k)}"
        assert 0 < k <= len(self.tokens), \
            f"next_candidates: k should be between 0 and {len(self.tokens)}"

        assert_model_is_loaded(self)
        prompt_tokens = self.llama.tokenize(prompt.encode('utf-8', errors='ignore'))
        self.llama.reset() # reset model state
        self.llama.eval(prompt_tokens)
        scores = self.llama.scores[len(prompt_tokens) - 1]

        # len(self.llama.scores) == self.context_length
        # len(self.llama.scores[i]) == len(self.tokens)
        
        # normalize scores with softmax
        # must normalize over all tokens in vocab, not just top k
        if self.verbose:
            print_verbose(f'calculating softmax over {len(scores)} values')
        normalized_scores: list[np.floating] = list(softmax(scores))

        # construct the final list
        i = 0
        token_probs_list: list[tuple[str, np.floating]] = []
        for tok_str in self.tokens:
            token_probs_list.append((tok_str, normalized_scores[i]))
            i += 1

        # return token_probs_list, sorted by probability, only top k
        return nlargest(k, token_probs_list, key=lambda x:x[1])


    def print_candidates(
        self,
        prompt: str,
        k: int,
        file: _SupportsWriteAndFlush = sys.stdout,
        flush: bool = False
    ) -> None:
        """
        Like `Model.candidates()`, but print the values instead
        of returning them
        """

        for _tuple in self.candidates(prompt, k):
            print(
                f"token {repr(_tuple[0])} has probability {_tuple[1]}",
                file=file,
                flush=flush
            )
        
        # if flush is False, then so far file is not flushed, but it should
        # always be flushed at the end of printing
        if not flush:
            file.flush()


def assert_model_is_loaded(model: Model) -> None:
    """
    Ensure the Model is fully constructed, such that
    `Model.llama._model.model is not None` is guaranteed to be `True`

    Raise ModelUnloadedException otherwise
    """
    if not hasattr(model, 'llama'):
        raise ModelUnloadedException(
            "webscout.Local.Model instance has no attribute 'llama'"
        )
    if not hasattr(model.llama, '_model'):
        raise ModelUnloadedException(
            "llama_cpp.Llama instance has no attribute '_model'"
        )
    if not hasattr(model.llama._model, 'model'):
        raise ModelUnloadedException(
            "llama_cpp._internals._LlamaModel instance has no attribute 'model'"
        )
    if model.llama._model.model is None:
        raise ModelUnloadedException(
            "llama_cpp._internals._LlamaModel.model is None"
        )
