import requests
import json
from typing import *

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent
class TypeGPT(Provider):
    """
    A class to interact with the TypeGPT.net API.  Improved to match webscout standards.
    """
    url = "https://chat.typegpt.net"
    working = True
    supports_message_history = True

    models = [
        # OpenAI Models
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-202201",
        "gpt-4o",
        "gpt-4o-2024-05-13",
        "o1-preview",
        
        # Claude Models
        "claude",
        "claude-3-5-sonnet",
        "claude-sonnet-3.5",
        "claude-3-5-sonnet-20240620",
        
        # Meta/LLaMA Models
        "@cf/meta/llama-2-7b-chat-fp16",
        "@cf/meta/llama-2-7b-chat-int8",
        "@cf/meta/llama-3-8b-instruct",
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/meta-llama/llama-2-7b-chat-hf-lora",
        "llama-3.1-405b",
        "llama-3.1-70b",
        "llama-3.1-8b",
        "meta-llama/Llama-2-7b-chat-hf",
        "meta-llama/Llama-3.1-70B-Instruct",
        "meta-llama/Llama-3.1-8B-Instruct",
        "meta-llama/Llama-3.2-11B-Vision-Instruct",
        "meta-llama/Llama-3.2-1B-Instruct",
        "meta-llama/Llama-3.2-3B-Instruct",
        "meta-llama/Llama-3.2-90B-Vision-Instruct",
        "meta-llama/Llama-Guard-3-8B",
        "meta-llama/Meta-Llama-3-70B-Instruct",
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        
        # Mistral Models
        "mistral",
        "mistral-large",
        "@cf/mistral/mistral-7b-instruct-v0.1",
        "@cf/mistral/mistral-7b-instruct-v0.2-lora",
        "@hf/mistralai/mistral-7b-instruct-v0.2",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "mistralai/Mixtral-8x22B-Instruct-v0.1",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        
        # Qwen Models
        "@cf/qwen/qwen1.5-0.5b-chat",
        "@cf/qwen/qwen1.5-1.8b-chat",
        "@cf/qwen/qwen1.5-7b-chat-awq",
        "@cf/qwen/qwen1.5-14b-chat-awq",
        "Qwen/Qwen2.5-3B-Instruct",
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        
        # Google/Gemini Models
        "@cf/google/gemma-2b-it-lora",
        "@cf/google/gemma-7b-it-lora",
        "@hf/google/gemma-7b-it",
        "google/gemma-1.1-2b-it",
        "google/gemma-1.1-7b-it",
        "gemini-pro",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash",
        
        # Cohere Models
        "c4ai-aya-23-35b",
        "c4ai-aya-23-8b",
        "command",
        "command-light",
        "command-light-nightly",
        "command-nightly",
        "command-r",
        "command-r-08-2024",
        "command-r-plus",
        "command-r-plus-08-2024",
        "rerank-english-v2.0",
        "rerank-english-v3.0",
        "rerank-multilingual-v2.0",
        "rerank-multilingual-v3.0",
        
        # Microsoft Models
        "@cf/microsoft/phi-2",
        "microsoft/DialoGPT-medium",
        "microsoft/Phi-3-medium-4k-instruct",
        "microsoft/Phi-3-mini-4k-instruct",
        "microsoft/Phi-3.5-mini-instruct",
        "microsoft/WizardLM-2-8x22B",
        
        # Yi Models
        "01-ai/Yi-1.5-34B-Chat",
        "01-ai/Yi-34B-Chat",
        
        # Specialized Models and Tools
        "@cf/deepseek-ai/deepseek-math-7b-base",
        "@cf/deepseek-ai/deepseek-math-7b-instruct",
        "@cf/defog/sqlcoder-7b-2",
        "@cf/openchat/openchat-3.5-0106",
        "@cf/thebloke/discolm-german-7b-v1-awq",
        "@cf/tiiuae/falcon-7b-instruct",
        "@cf/tinyllama/tinyllama-1.1b-chat-v1.0",
        "@hf/nexusflow/starling-lm-7b-beta",
        "@hf/nousresearch/hermes-2-pro-mistral-7b",
        "@hf/thebloke/deepseek-coder-6.7b-base-awq",
        "@hf/thebloke/deepseek-coder-6.7b-instruct-awq",
        "@hf/thebloke/llama-2-13b-chat-awq",
        "@hf/thebloke/llamaguard-7b-awq",
        "@hf/thebloke/neural-chat-7b-v3-1-awq",
        "@hf/thebloke/openhermes-2.5-mistral-7b-awq",
        "@hf/thebloke/zephyr-7b-beta-awq",
        "AndroidDeveloper",
        "AngularJSAgent",
        "AzureAgent",
        "BitbucketAgent",
        "DigitalOceanAgent",
        "DockerAgent",
        "ElectronAgent",
        "ErlangAgent",
        "FastAPIAgent",
        "FirebaseAgent",
        "FlaskAgent",
        "FlutterAgent",
        "GitAgent",
        "GitlabAgent",
        "GoAgent",
        "GodotAgent",
        "GoogleCloudAgent",
        "HTMLAgent",
        "HerokuAgent",
        "ImageGeneration",
        "JavaAgent",
        "JavaScriptAgent",
        "MongoDBAgent",
        "Next.jsAgent",
        "PyTorchAgent",
        "PythonAgent",
        "ReactAgent",
        "RepoMap",
        "SwiftDeveloper",
        "XcodeAgent",
        "YoutubeAgent",
        "blackboxai",
        "blackboxai-pro",
        "builderAgent",
        "dify",
        "flux",
        "openchat/openchat-3.6-8b",
        "rtist",
        "searchgpt",
        "sur",
        "sur-mistral",
        "unity"
    ]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 4000,  # Set a reasonable default
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "claude-3-5-sonnet-20240620",
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.5,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1,
    ):
        """Initializes the TypeGPT API client."""
        if model not in self.models:
            raise ValueError(f"Invalid model: {model}. Choose from: {', '.join(self.models)}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://chat.typegpt.net/api/openai/v1/chat/completions"
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p
        self.headers = {
            "authority": "chat.typegpt.net",
            "accept": "application/json, text/event-stream",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://chat.typegpt.net",
            "referer": "https://chat.typegpt.net/",
            "user-agent": LitAgent().random()
        }


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
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.session.proxies = proxies

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any] | Generator:
        """Sends a prompt to the TypeGPT.net API and returns the response."""
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise exceptions.FailedToGenerateResponseError(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )


        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt}
            ],
            "stream": stream,
            "model": self.model,
            "temperature": self.temperature,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens_to_sample,
        }
        def for_stream():
            response = self.session.post(
                self.api_endpoint, headers=self.headers, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )
            message_load = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        line = line[6:]  # Remove "data: " prefix
                        # Skip [DONE] message
                        if line.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(line)
                            
                            # Extract and yield only new content
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    new_content = delta['content']
                                    message_load += new_content
                                    # Yield only the new content
                                    yield dict(text=new_content) if not raw else new_content
                                    self.last_response = dict(text=message_load)

                        except json.JSONDecodeError:
                            continue
            self.conversation.update_chat_history(prompt, self.get_message(self.last_response))

        def for_non_stream():

            response = self.session.post(self.api_endpoint, headers=self.headers, json=payload)
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Request failed - {response.status_code}: {response.text}"
                )
            self.last_response = response.json()
            self.conversation.update_chat_history(prompt, self.get_message(self.last_response))
            return self.last_response


        return for_stream() if stream else for_non_stream()


    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | Generator[str, None, None]:
        """Generate response `str` or stream."""

        if stream:
            gen = self.ask(
                prompt, stream=True, optimizer=optimizer, conversationally=conversationally
            )
            for chunk in gen:
                yield self.get_message(chunk)  # Extract text from streamed chunks
        else:
            return self.get_message(self.ask(prompt, stream=False, optimizer=optimizer, conversationally=conversationally))

    def get_message(self, response: Dict[str, Any]) -> str:
        """Retrieves message from response."""
        if isinstance(response, str): #Handle raw responses
            return response
        elif isinstance(response, dict):
            assert isinstance(response, dict), "Response should be of dict data-type only"
            return response.get("text", "") #Extract text from dictionary response
        else:
            raise TypeError("Invalid response type. Expected str or dict.")


if __name__ == "__main__":
       
    ai = TypeGPT(model="claude-3-5-sonnet-20240620")
    response = ai.chat("hi", stream=True)
    for chunks in response:
        print(chunks, end="", flush=True)