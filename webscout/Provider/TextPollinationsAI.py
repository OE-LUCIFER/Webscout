import requests
import json
from typing import Union, Any, Dict, Generator
from webscout.AIutel import Optimizers, Conversation, AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent as Lit

class TextPollinationsAI(Provider):
    """
    A class to interact with the Pollinations AI API.
    """

    AVAILABLE_MODELS = [
        "openai",              # OpenAI GPT-4o-mini
        "openai-large",        # OpenAI GPT-4o
        "openai-reasoning",    # OpenAI o1-mini
        "qwen-coder",          # Qwen 2.5 Coder 32B
        "llama",               # Llama 3.3 70B
        "mistral",             # Mistral Nemo
        "unity",               # Unity with Mistral Large
        "midijourney",         # Midijourney musical transformer
        "rtist",               # Rtist image generator
        "searchgpt",           # SearchGPT with realtime search
        "evil",                # Evil Mode - Experimental
        # "deepseek",            # DeepSeek-V3 >>>> NOT WORKING
        "claude-hybridspace",  # Claude Hybridspace
        "deepseek-r1",         # DeepSeek-R1 Distill Qwen 32B
        # "deepseek-reasoner",   # DeepSeek R1 - Full >>>> NOT WORKING
        # "llamalight",          # Llama 3.1 8B Instruct >>>> NOT WORKING
        # "llamaguard",          # Llamaguard 7B AWQ >>>> NOT WORKING
        "gemini",              # Gemini 2.0 Flash
        "gemini-thinking",     # Gemini 2.0 Flash Thinking
        "hormoz",              # Hormoz 8b
        "hypnosis-tracy",      # Hypnosis Tracy
        "sur",                 # Sur AI Assistant
        "sur-mistral",         # Sur AI Assistant (Mistral)
        # "llama-scaleway",      # Llama (Scaleway) >>>> NOT WORKING
        "phi",                 # Phi model
        # "openai-audio"         # OpenAI Audio model >>>> NOT WORKING
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 8096,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "openai-large",
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """Initializes the TextPollinationsAI API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://text.pollinations.ai/openai"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': Lit().random(),
            'Content-Type': 'application/json',
        }
        
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

        self.__available_optimizers = (
            method for method in dir(Optimizers)
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
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator[Any, None, None]][Dict[str, Any], None, None]:
        """Chat with AI"""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ],
            "model": self.model,
            "stream": stream,
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=self.timeout
            )

            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8').strip()
                    if line == "data: [DONE]":
                        break
                    if line.startswith('data: '):
                        try:
                            json_data = json.loads(line[6:])
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                choice = json_data['choices'][0]
                                if 'delta' in choice and 'content' in choice['delta']:
                                    content = choice['delta']['content']
                                else:
                                    content = ""
                                full_response += content
                                yield content if raw else dict(text=content)
                        except json.JSONDecodeError:
                            continue

            self.last_response.update(dict(text=full_response))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response as a string"""
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
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)
    
    # Test all available models
    working = 0
    total = len(TextPollinationsAI.AVAILABLE_MODELS)
    
    for model in TextPollinationsAI.AVAILABLE_MODELS:
        try:
            test_ai = TextPollinationsAI(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            for chunk in response:
                response_text += chunk
                print(f"\r{model:<50} {'Testing...':<10}", end="", flush=True)
            
            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Truncate response if too long
                display_text = response_text.strip()[:50] + "..." if len(response_text.strip()) > 50 else response_text.strip()
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")
