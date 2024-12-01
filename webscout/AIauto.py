from webscout.AIbase import Provider
from webscout.g4f import GPT4FREE, TestProviders
from webscout.exceptions import AllProvidersFailure
from webscout.Litlogger import Litlogger, LogFormat, ColorScheme
from typing import Union, Any, Dict, Generator
import importlib
import pkgutil
import random
import inspect

# Initialize LitLogger with cyberpunk theme
logger = Litlogger(
    name="AIauto",
    format=LogFormat.DETAILED,
    color_scheme=ColorScheme.CYBERPUNK
)

def load_providers():
    provider_map = {}
    api_key_providers = set()
    provider_package = importlib.import_module("webscout.Provider")
    
    for _, module_name, _ in pkgutil.iter_modules(provider_package.__path__):
        try:
            module = importlib.import_module(f"webscout.Provider.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Provider) and attr != Provider:
                    provider_map[attr_name.upper()] = attr
                    # Check if the provider needs an API key
                    if 'api_key' in inspect.signature(attr.__init__).parameters:
                        api_key_providers.add(attr_name.upper())
                        logger.debug(f"Provider {attr_name} requires API key")
            logger.success(f"Loaded provider module: {module_name}")
        except Exception as e:
            logger.error(f"Failed to load provider {module_name}: {str(e)}")
    
    logger.info(f"Total providers loaded: {len(provider_map)}")
    logger.info(f"API key providers: {len(api_key_providers)}")
    return provider_map, api_key_providers

provider_map, api_key_providers = load_providers()

class AUTO(Provider):
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        exclude: list[str] = [],
    ):
        self.provider = None
        self.provider_name = None
        self.is_conversation = is_conversation
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.intro = intro
        self.filepath = filepath
        self.update_file = update_file
        self.proxies = proxies
        self.history_offset = history_offset
        self.act = act
        self.exclude = [e.upper() for e in exclude]

    @property
    def last_response(self) -> dict[str, Any]:
        return self.provider.last_response if self.provider else {}

    @property
    def conversation(self) -> object:
        return self.provider.conversation if self.provider else None

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        run_new_test: bool = False,
    ) -> Union[Dict, Generator]:
        ask_kwargs = {
            "prompt": prompt,
            "stream": stream,
            "raw": raw,
            "optimizer": optimizer,
            "conversationally": conversationally,
        }

        # Filter out API key required providers and excluded providers
        available_providers = [
            (name, cls) for name, cls in provider_map.items()
            if name not in api_key_providers and name not in self.exclude
        ]

        # Shuffle the list of available providers
        random.shuffle(available_providers)

        # Try webscout-based providers
        for provider_name, provider_class in available_providers:
            try:
                self.provider_name = f"webscout-{provider_name}"
                logger.info(f"Trying provider: {self.provider_name}")
                
                self.provider = provider_class(
                    is_conversation=self.is_conversation,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                    intro=self.intro,
                    filepath=self.filepath,
                    update_file=self.update_file,
                    proxies=self.proxies,
                    history_offset=self.history_offset,
                    act=self.act,
                )
                response = self.provider.ask(**ask_kwargs)
                logger.success(f"Successfully used provider: {self.provider_name}")
                return response
            except Exception as e:
                logger.warning(f"Provider {self.provider_name} failed: {str(e)}")
                continue

        # Try GPT4FREE providers
        gpt4free_providers = TestProviders(timeout=self.timeout).get_results(run=run_new_test)
        random.shuffle(gpt4free_providers)
        
        for provider_info in gpt4free_providers:
            if provider_info["name"].upper() in self.exclude:
                continue
            try:
                self.provider_name = f"g4f-{provider_info['name']}"
                logger.info(f"Trying provider: {self.provider_name}")
                
                self.provider = GPT4FREE(
                    provider=provider_info["name"],
                    is_conversation=self.is_conversation,
                    max_tokens=self.max_tokens,
                    intro=self.intro,
                    filepath=self.filepath,
                    update_file=self.update_file,
                    proxies=self.proxies,
                    history_offset=self.history_offset,
                    act=self.act,
                )

                response = self.provider.ask(**ask_kwargs)
                logger.success(f"Successfully used provider: {self.provider_name}")
                return response
            except Exception as e:
                logger.warning(f"Provider {self.provider_name} failed: {str(e)}")
                continue

        # If we get here, all providers failed
        logger.error("All providers failed to process the request")
        raise AllProvidersFailure("All providers failed to process the request")

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        run_new_test: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        response = self.ask(
            prompt,
            stream,
            optimizer=optimizer,
            conversationally=conversationally,
            run_new_test=run_new_test,
        )
        
        if stream:
            return (self.get_message(chunk) for chunk in response)
        else:
            return self.get_message(response)

    def get_message(self, response: dict) -> str:
        assert self.provider is not None, "Chat with AI first"
        return self.provider.get_message(response)
if __name__ == "__main__":
    auto = AUTO()

    response = auto.chat("Hello, how are you?")
    print(response)
