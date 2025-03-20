import requests
import json
from typing import *
import requests.exceptions

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent

class TypeGPT(Provider):
    """
    A class to interact with the TypeGPT.net API. Improved to match webscout standards.
    """
    url = "https://chat.typegpt.net"

    AVAILABLE_MODELS = [
        # OpenAI Models
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-202201",
        "gpt-4o",
        "gpt-4o-2024-05-13",
        "gpt-4o-2024-11-20",
        "gpt-4o-mini",
        "gpt-4o-mini-2024-07-18",
        # "gpt-4o-mini-ddg", >>>> NOT WORKING
        "o1",
        # "o1-mini-2024-09-12", >>>> NOT WORKING
        "o1-preview",
        "o3-mini",
        "chatgpt-4o-latest",
        
        # Claude Models
        # "claude", >>>> NOT WORKING
        "claude-3-5-sonnet",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-sonnet-x",
        # "claude-3-haiku-ddg", >>>> NOT WORKING
        "claude-hybridspace",
        "claude-sonnet-3.5",
        "Claude-sonnet-3.7",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3.7-sonnet",
        
        # Meta/LLaMA Models
        "@cf/meta/llama-2-7b-chat-fp16",
        "@cf/meta/llama-2-7b-chat-int8",
        "@cf/meta/llama-3-8b-instruct",
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        # "@cf/meta-llama/llama-2-7b-chat-hf-lora", >>>> NOT WORKING
        "llama-3.1-405b",
        "llama-3.1-70b",
        # "llama-3.1-70b-ddg", >>>> NOT WORKING
        "llama-3.1-8b",
        # "llama-scaleway", >>>> NOT WORKING
        "llama3.1-8b", # >>>> NOT WORKING
        "llama3.3-70b",
        # "llamalight", >>>> NOT WORKING
        "Meta-Llama-3.1-405B-Instruct-Turbo",
        "Meta-Llama-3.3-70B-Instruct-Turbo",
        # "meta-llama/Llama-2-7b-chat-hf", >>>> NOT WORKING
        # "meta-llama/Llama-3.1-70B-Instruct", >>>> NOT WORKING
        # "meta-llama/Llama-3.1-8B-Instruct", >>>> NOT WORKING
        "meta-llama/Llama-3.2-11B-Vision-Instruct",
        # "meta-llama/Llama-3.2-1B-Instruct", >>>> NOT WORKING
        # "meta-llama/Llama-3.2-3B-Instruct", >>>> NOT WORKING
        "meta-llama/Llama-3.2-90B-Vision-Instruct",
        "meta-llama/Llama-3.3-70B-Instruct",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        # "meta-llama/Llama-Guard-3-8B", >>>> NOT WORKING
        # "meta-llama/Meta-Llama-3-70B-Instruct", >>>> NOT WORKING
        # "meta-llama/Meta-Llama-3-8B-Instruct", >>>> NOT WORKING
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        
        # Mistral Models
        "mistral",
        "mistral-large",
        "@cf/mistral/mistral-7b-instruct-v0.1",
        # "@cf/mistral/mistral-7b-instruct-v0.2-lora", >>>> NOT WORKING
        "@hf/mistralai/mistral-7b-instruct-v0.2",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "mistralai/Mixtral-8x22B-Instruct-v0.1",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        # "mixtral-8x7b-ddg", >>>> NOT WORKING
        "Mistral-7B-Instruct-v0.2",
        
        # Qwen Models
        "@cf/qwen/qwen1.5-0.5b-chat",
        "@cf/qwen/qwen1.5-1.8b-chat",
        "@cf/qwen/qwen1.5-14b-chat-awq",
        "@cf/qwen/qwen1.5-7b-chat-awq",
        "Qwen/Qwen2.5-3B-Instruct",
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "Qwen/Qwen2-72B-Instruct",
        "Qwen/QwQ-32B",
        "Qwen/QwQ-32B-Preview",
        "Qwen2.5-72B-Instruct",
        "qwen",
        "qwen-coder",
        # "Qwen-QwQ-32B-Preview", >>>> NOT WORKING
        
        # Google/Gemini Models
        # "@cf/google/gemma-2b-it-lora", >>>> NOT WORKING
        # "@cf/google/gemma-7b-it-lora", >>>> NOT WORKING
        "@hf/google/gemma-7b-it",
        "google/gemma-1.1-2b-it",
        "google/gemma-1.1-7b-it",
        "gemini-pro",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash",
        "gemini-flash-2.0",
        "gemini-thinking",
        
        # Microsoft Models
        "@cf/microsoft/phi-2",
        "microsoft/DialoGPT-medium",
        "microsoft/Phi-3-medium-4k-instruct",
        "microsoft/Phi-3-mini-4k-instruct",
        "microsoft/Phi-3.5-mini-instruct",
        "microsoft/phi-4",
        "microsoft/WizardLM-2-8x22B",
        
        # Yi Models
        "01-ai/Yi-1.5-34B-Chat",
        # "01-ai/Yi-34B-Chat", >>>> NOT WORKING
        
        # DeepSeek Models
        "@cf/deepseek-ai/deepseek-math-7b-base",
        "@cf/deepseek-ai/deepseek-math-7b-instruct",
        "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
        "deepseek",
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        # "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", >>>> NOT WORKING
        # "deepseek-ai/DeepSeek-V2.5", >>>> NOT WORKING
        "deepseek-llm-67b-chat",
        "deepseek-r1",
        "deepseek-r1-distill-llama-70b",
        # "deepseek-reasoner", >>>> NOT WORKING
        "deepseek-v3",
        
        # Specialized Models and Tools
        "@cf/defog/sqlcoder-7b-2",
        "@cf/thebloke/discolm-german-7b-v1-awq",
        "@cf/tiiuae/falcon-7b-instruct",
        # "@cf/tinyllama/tinyllama-1.1b-chat-v1.0", >>>> NOT WORKING
        # "@hf/nexusflow/starling-lm-7b-beta", >>>> NOT WORKING
        # "@hf/nousresearch/hermes-2-pro-mistral-7b", >>>> NOT WORKING
        # "@hf/thebloke/deepseek-coder-6.7b-base-awq", >>>> NOT WORKING
        # "@hf/thebloke/deepseek-coder-6.7b-instruct-awq", >>>> NOT WORKING
        # "@hf/thebloke/llama-2-13b-chat-awq", >>>> NOT WORKING
        # "@hf/thebloke/llamaguard-7b-awq", >>>> NOT WORKING
        # "@hf/thebloke/mistral-7b-instruct-v0.1-awq", >>>> NOT WORKING
        # "@hf/thebloke/neural-chat-7b-v3-1-awq", >>>> NOT WORKING
        # "@hf/thebloke/openhermes-2.5-mistral-7b-awq", >>>> NOT WORKING
        # "@hf/thebloke/zephyr-7b-beta-awq", >>>> NOT WORKING
        
        # Development Agents
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
        # "YoutubeAgent", >>>> NOT WORKING
        
        # Other Models
        "blackboxai",
        "blackboxai-pro",
        "builderAgent",
        # "Cipher-20b", >>>> NOT WORKING
        # "dify", >>>> NOT WORKING
        "flux",
        # "flux-1-schnell", >>>> NOT WORKING
        # "HelpingAI-15B", >>>> NOT WORKING
        # "HelpingAI2-3b", >>>> NOT WORKING
        # "HelpingAI2-6B", >>>> NOT WORKING
        # "HelpingAI2-9B", >>>> NOT WORKING
        # "HelpingAI2.5-10B", >>>> NOT WORKING
        # "Helpingai2.5-10b-1m", >>>> NOT WORKING
        # "HelpingAI2.5-2B", >>>> NOT WORKING
        # "HELVETE", >>>> NOT WORKING
        # "HELVETE-X", >>>> NOT WORKING
        # "evil", >>>> NOT WORKING
        # "Image-Generator", >>>> NOT WORKING
        # "Image-Generator-NSFW", >>>> NOT WORKING
        # "midijourney", >>>> NOT WORKING
        # "Niansuh", >>>> NOT WORKING
        # "niansuh-t1", >>>> NOT WORKING
        # "Nous-Hermes-2-Mixtral-8x7B-DPO", >>>> NOT WORKING
        # "NousResearch/Hermes-3-Llama-3.1-8B", >>>> NOT WORKING
        # "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO", >>>> NOT WORKING
        # "nvidia/Llama-3.1-Nemotron-70B-Instruct", >>>> NOT WORKING
        # "openai", >>>> NOT WORKING
        # "openai-audio", >>>> NOT WORKING
        # "openai-large", >>>> NOT WORKING
        # "openai-reasoning", >>>> NOT WORKING
        # "openai/whisper-large-v3", >>>> NOT WORKING
        # "openai/whisper-large-v3-turbo", >>>> NOT WORKING
        # "openbmb/MiniCPM-Llama3-V-2_5", >>>> NOT WORKING
        # "openchat/openchat-3.6-8b", >>>> NOT WORKING
        # "p1", >>>> NOT WORKING
        # "phi", >>>> NOT WORKING
        # "Phi-4-multilmodal-instruct", >>>> NOT WORKING
        # "Priya-3B", >>>> NOT WORKING
        # "rtist", >>>> NOT WORKING
        # "searchgpt", >>>> NOT WORKING
        # "sur", >>>> NOT WORKING
        # "sur-mistral", >>>> NOT WORKING
        # "tiiuae/falcon-7b-instruct", >>>> NOT WORKING
        # "TirexAi", >>>> NOT WORKING
        # "unity", >>>> NOT WORKING
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
        model: str = "gpt-4o",
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.5,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1,
    ):
        """Initializes the TypeGPT API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {', '.join(self.AVAILABLE_MODELS)}")

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
        self.conversation = Conversation(is_conversation, self.max_tokens_to_sample, filepath, update_file)
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
            try:
                response = self.session.post(
                    self.api_endpoint, headers=self.headers, json=payload, stream=True, timeout=self.timeout
                )
            except requests.exceptions.ConnectionError as ce:
                raise exceptions.FailedToGenerateResponseError(
                    f"Network connection failed. Check your firewall or antivirus settings. Original error: {ce}"
                ) from ce

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
            try:
                response = self.session.post(self.api_endpoint, headers=self.headers, json=payload, timeout=self.timeout)
            except requests.exceptions.ConnectionError as ce:
                raise exceptions.FailedToGenerateResponseError(
                    f"Network connection failed. Check your firewall or antivirus settings. Original error: {ce}"
                ) from ce

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
        """Generate response string or stream."""
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
        if isinstance(response, str):  # Handle raw responses
            return response
        elif isinstance(response, dict):
            assert isinstance(response, dict), "Response should be of dict data-type only"
            return response.get("text", "")  # Extract text from dictionary response
        else:
            raise TypeError("Invalid response type. Expected str or dict.")

if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)
    
    # Test all available models
    working = 0
    total = len(TypeGPT.AVAILABLE_MODELS)
    
    for model in TypeGPT.AVAILABLE_MODELS:
        try:
            test_ai = TypeGPT(model=model, timeout=60)
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
    
