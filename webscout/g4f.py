import g4f
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider, AsyncProvider
from webscout.AIutel import available_providers
from typing import Any, AsyncGenerator

g4f.debug.version_check = False

working_providers = available_providers

completion_allowed_models = [
    "code-davinci-002",
    "text-ada-001",
    "text-babbage-001",
    "text-curie-001",
    "text-davinci-002",
    "text-davinci-003",
]

default_models = {
    "completion": "text-davinci-003",
    "chat_completion": "gpt-3.5-turbo",
}

default_provider = "Koala"

class AsyncGPT4FREE(AsyncProvider):
    def __init__(
        self,
        provider: str = default_provider,
        is_conversation: bool = True,
        auth: str = None,
        max_tokens: int = 600,
        model: str = None,
        ignore_working: bool = False,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Initialies GPT4FREE

        Args:
            provider (str, optional): gpt4free based provider name. Defaults to Koala.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            auth (str, optional): Authentication value for the provider incase it needs. Defaults to None.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            model (str, optional): LLM model name. Defaults to text-davinci-003|gpt-3.5-turbo.
            ignore_working (bool, optional): Ignore working status of the provider. Defaults to False.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        assert provider in available_providers, (
            f"Provider '{provider}' is not yet supported. "
            f"Try others like {', '.join(available_providers)}"
        )
        if model is None:
            model = default_models["chat_completion"]

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation,
            self.max_tokens_to_sample,
            filepath,
            update_file,
        )
        self.conversation.history_offset = history_offset
        self.model = model
        self.provider = provider
        self.ignore_working = ignore_working
        self.auth = auth
        self.proxy = None if not proxies else list(proxies.values())[0]

    def __str__(self):
        return f"AsyncGPTFREE(provider={self.provider})"

    async def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict | AsyncGenerator:
        """Chat with AI asynchronously.

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
           dict|AsyncGenerator : ai content
        ```json
        {
          "text" : "How may I help you today?"
        }
        ```
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        payload = dict(
            model=self.model,
            provider=self.provider,  # g4f.Provider.Aichat,
            messages=[{"role": "user", "content": conversation_prompt}],
            stream=True,
            ignore_working=self.ignore_working,
            auth=self.auth,
            proxy=self.proxy,
            timeout=self.timeout,
        )

        async def format_response(response):
            return dict(text=response)

        async def for_stream():
            previous_chunks = ""
            response = g4f.ChatCompletion.create_async(**payload)

            async for chunk in response:
                previous_chunks += chunk
                formatted_resp = await format_response(previous_chunks)
                self.last_response.update(formatted_resp)
                yield previous_chunks if raw else formatted_resp

            self.conversation.update_chat_history(
                prompt,
                previous_chunks,
            )

        async def for_non_stream():
            async for _ in for_stream():
                pass
            return self.last_response

        return for_stream() if stream else await for_non_stream()

    async def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict | AsyncGenerator:
        """Generate response `str` asynchronously.
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str|AsyncGenerator: Response generated
        """

        async def for_stream():
            async_ask = await self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            )
            async for response in async_ask:
                yield await self.get_message(response)

        async def for_non_stream():
            return await self.get_message(
                await self.ask(
                    prompt,
                    False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
            )

        return for_stream() if stream else await for_non_stream()

    async def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]
class GPT4FREE(Provider):
    def __init__(
        self,
        provider: str = default_provider,
        is_conversation: bool = True,
        auth: str = None,
        max_tokens: int = 600,
        model: str = None,
        chat_completion: bool = True,
        ignore_working: bool = True,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
    ):
        """Initialies GPT4FREE

        Args:
            provider (str, optional): gpt4free based provider name. Defaults to Koala.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            auth (str, optional): Authentication value for the provider incase it needs. Defaults to None.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            model (str, optional): LLM model name. Defaults to text-davinci-003|gpt-3.5-turbo.
            chat_completion(bool, optional): Provide native auto-contexting (conversationally). Defaults to False.
            ignore_working (bool, optional): Ignore working status of the provider. Defaults to False.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        assert provider in available_providers, (
            f"Provider '{provider}' is not yet supported. "
            f"Try others like {', '.join(available_providers)}"
        )
        if model is None:
            model = (
                default_models["chat_completion"]
                if chat_completion
                else default_models["completion"]
            )

        elif not chat_completion:
            assert model in completion_allowed_models, (
                f"Model '{model}' is not yet supported for completion. "
                f"Try other models like {', '.join(completion_allowed_models)}"
            )
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or Conversation.intro
        )
        self.conversation = Conversation(
            False if chat_completion else is_conversation,
            self.max_tokens_to_sample,
            filepath,
            update_file,
        )
        self.conversation.history_offset = history_offset
        self.model = model
        self.provider = provider
        self.chat_completion = chat_completion
        self.ignore_working = ignore_working
        self.auth = auth
        self.proxy = None if not proxies else list(proxies.values())[0]
        self.__chat_class = g4f.ChatCompletion if chat_completion else g4f.Completion

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with AI

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
           dict : {}
        ```json
        {
          "text" : "How may I help you today?"
        }
        ```
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        def payload():
            if self.chat_completion:
                return dict(
                    model=self.model,
                    provider=self.provider,  # g4f.Provider.Aichat,
                    messages=[{"role": "user", "content": conversation_prompt}],
                    stream=stream,
                    ignore_working=self.ignore_working,
                    auth=self.auth,
                    proxy=self.proxy,
                    timeout=self.timeout,
                )

            else:
                return dict(
                    model=self.model,
                    prompt=conversation_prompt,
                    provider=self.provider,
                    stream=stream,
                    ignore_working=self.ignore_working,
                    auth=self.auth,
                    proxy=self.proxy,
                    timeout=self.timeout,
                )

        def format_response(response):
            return dict(text=response)

        def for_stream():
            previous_chunks = ""
            response = self.__chat_class.create(**payload())

            for chunk in response:
                previous_chunks += chunk
                formatted_resp = format_response(previous_chunks)
                self.last_response.update(formatted_resp)
                yield previous_chunks if raw else formatted_resp

            self.conversation.update_chat_history(
                prompt,
                previous_chunks,
            )

        def for_non_stream():
            response = self.__chat_class.create(**payload())
            formatted_resp = format_response(response)

            self.last_response.update(formatted_resp)
            self.conversation.update_chat_history(prompt, response)

            return response if raw else formatted_resp

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
        """

        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt,
                    False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]
from pathlib import Path
from webscout.AIutel import default_path
from json import dump, load
from time import time
from threading import Thread as thr
from functools import wraps
from rich.progress import Progress
import logging

results_path = Path(default_path) / "provider_test.json"


def exception_handler(func):

    @wraps(func)
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pass

    return decorator


@exception_handler
def is_working(provider: str) -> bool:
    """Test working status of a provider

    Args:
        provider (str): Provider name

    Returns:
        bool: is_working status
    """
    bot = GPT4FREE(provider=provider, is_conversation=False)
    text = bot.chat("hello")
    assert isinstance(text, str)
    assert bool(text.strip())
    assert "</" not in text
    assert ":" not in text
    assert len(text) > 2
    return True


class TestProviders:

    def __init__(
        self,
        test_at_once: int = 5,
        quiet: bool = False,
        timeout: int = 20,
        selenium: bool = False,
        do_log: bool = True,
    ):
        """Constructor

        Args:
            test_at_once (int, optional): Test n providers at once. Defaults to 5.
            quiet (bool, optinal): Disable stdout. Defaults to False.
            timout (int, optional): Thread timeout for each provider. Defaults to 20.
            selenium (bool, optional): Test even selenium dependent providers. Defaults to False.
            do_log (bool, optional): Flag to control logging. Defaults to True.
        """
        self.test_at_once: int = test_at_once
        self.quiet = quiet
        self.timeout = timeout
        self.do_log = do_log
        self.__logger = logging.getLogger(__name__)
        self.working_providers: list = [
            provider.__name__
            for provider in g4f.Provider.__providers__
            if provider.working
        ]

        if not selenium:
            import g4f.Provider.selenium as selenium_based
            from g4f import webdriver

            webdriver.has_requirements = False
            selenium_based_providers: list = dir(selenium_based)
            for provider in self.working_providers:
                try:
                    selenium_based_providers.index(provider)
                except ValueError:
                    pass
                else:
                    self.__log(
                        10, f"Dropping provider - {provider} - [Selenium dependent]"
                    )
                    self.working_providers.remove(provider)

        self.results_path: Path = results_path
        self.__create_empty_file(ignore_if_found=True)
        self.results_file_is_empty: bool = False

    def __log(
        self,
        level: int,
        message: str,
    ):
        """class logger"""
        if self.do_log:
            self.__logger.log(level, message)
        else:
            pass

    def __create_empty_file(self, ignore_if_found: bool = False):
        if ignore_if_found and self.results_path.is_file():
            return
        with self.results_path.open("w") as fh:
            dump({"results": []}, fh)
        self.results_file_is_empty = True

    def test_provider(self, name: str):
        """Test each provider and save successful ones

        Args:
            name (str): Provider name
        """

        try:
            bot = GPT4FREE(provider=name, is_conversation=False)
            start_time = time()
            text = bot.chat("hello there")
            assert isinstance(text, str), "Non-string response returned"
            assert bool(text.strip()), "Empty string"
            assert "</" not in text, "Html code returned."
            assert ":" not in text, "Json formatted response returned"
            assert len(text) > 2
        except Exception as e:
            pass
        else:
            self.results_file_is_empty = False
            with self.results_path.open() as fh:
                current_results = load(fh)
            new_result = dict(time=time() - start_time, name=name)
            current_results["results"].append(new_result)
            self.__log(20, f"Test result - {new_result['name']} - {new_result['time']}")

            with self.results_path.open("w") as fh:
                dump(current_results, fh)

    @exception_handler
    def main(
        self,
    ):
        self.__create_empty_file()
        threads = []
        # Create a progress bar
        total = len(self.working_providers)
        with Progress() as progress:
            self.__log(20, f"Testing {total} providers : {self.working_providers}")
            task = progress.add_task(
                f"[cyan]Testing...[{self.test_at_once}]",
                total=total,
                visible=self.quiet == False,
            )
            while not progress.finished:
                for count, provider in enumerate(self.working_providers, start=1):
                    t1 = thr(
                        target=self.test_provider,
                        args=(provider,),
                    )
                    t1.start()
                    if count % self.test_at_once == 0 or count == len(provider):
                        for t in threads:
                            try:
                                t.join(self.timeout)
                            except Exception as e:
                                pass
                        threads.clear()
                    else:
                        threads.append(t1)
                    progress.update(task, advance=1)

    def get_results(self, run: bool = False, best: bool = False) -> list[dict]:
        """Get test results

        Args:
            run (bool, optional): Run the test first. Defaults to False.
            best (bool, optional): Return name of the best provider. Defaults to False.

        Returns:
            list[dict]|str: Test results.
        """
        if run or self.results_file_is_empty:
            self.main()

        with self.results_path.open() as fh:
            results: dict = load(fh)

        results = results["results"]
        if not results:
            if run:
                raise Exception("Unable to find working g4f provider")
            else:
                self.__log(30, "Hunting down working g4f providers.")
                return self.get_results(run=True, best=best)

        time_list = []

        sorted_list = []
        for entry in results:
            time_list.append(entry["time"])

        time_list.sort()

        for time_value in time_list:
            for entry in results:
                if entry["time"] == time_value:
                    sorted_list.append(entry)
        return sorted_list[0]["name"] if best else sorted_list

    @property
    def best(self):
        """Fastest provider overally"""
        return self.get_results(run=False, best=True)

    @property
    def auto(self):
        """Best working provider"""
        for result in self.get_results(run=False, best=False):
            self.__log(20, "Confirming working status of provider : " + result["name"])
            if is_working(result["name"]):
                return result["name"]