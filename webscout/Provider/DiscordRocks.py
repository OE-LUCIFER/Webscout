import requests
import json
from typing import Any, AsyncGenerator, Dict

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import  Provider, AsyncProvider
from webscout import exceptions


class DiscordRocks(Provider):
    """
    A class to interact with the DiscordRocks API.
    """

    available_models = [
        "claude-3-haiku-20240307",
        "claude-3-sonnet-20240229",
        "claude-3-5-sonnet-20240620",
        "claude-3-opus-20240229",
        "gpt-4",
        "gpt-4-0613",
        "gpt-4-turbo",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4o",
        "llama-3-70b-chat",
        "llama-3-70b-chat-turbo",
        "llama-3-8b-chat",
        "llama-3-8b-chat-turbo",
        "llama-3-70b-chat-lite",
        "llama-3-8b-chat-lite",
        "llama-2-70b-chat",
        "llama-2-13b-chat",
        "llama-2-7b-chat",
        "llama-3.1-405b-turbo",
        "llama-3.1-70b-turbo",
        "llama-3.1-8b-turbo",
        "LlamaGuard-2-8b",
        "Yi-34B-Chat",
        "Yi-34B",
        "Yi-6B",
        "Mixtral-8x7B-v0.1",
        "Mixtral-8x22B",
        "Mixtral-8x7B-Instruct-v0.1",
        "Mixtral-8x22B-Instruct-v0.1",
        "Mistral-7B-Instruct-v0.1",
        "Mistral-7B-Instruct-v0.2",
        "Mistral-7B-Instruct-v0.3",
        "openchat-3.5",
        "WizardLM-13B-V1.2",
        "WizardCoder-Python-34B-V1.0",
        "Qwen1.5-0.5B-Chat",
        "Qwen1.5-1.8B-Chat",
        "Qwen1.5-4B-Chat",
        "Qwen1.5-7B-Chat",
        "Qwen1.5-14B-Chat",
        "Qwen1.5-72B-Chat",
        "Qwen1.5-110B-Chat",
        "Qwen2-72B-Instruct",
        "gemma-2b-it",
        "gemma-7b-it",
        "gemma-2b",
        "gemma-7b",
        "dbrx-instruct",
        "vicuna-7b-v1.5",
        "vicuna-13b-v1.5",
        "dolphin-2.5-mixtral-8x7b",
        "deepseek-coder-33b-instruct",
        "deepseek-coder-67b-instruct",
        "deepseek-llm-67b-chat",
        "Nous-Capybara-7B-V1p9",
        "Nous-Hermes-2-Mixtral-8x7B-DPO",
        "Nous-Hermes-2-Mixtral-8x7B-SFT",
        "Nous-Hermes-llama-2-7b",
        "Nous-Hermes-Llama2-13b",
        "Nous-Hermes-2-Yi-34B",
        "Mistral-7B-OpenOrca",
        "alpaca-7b",
        "OpenHermes-2-Mistral-7B",
        "OpenHermes-2.5-Mistral-7B",
        "phi-2",
        "phi-3",
        "WizardLM-2-8x22B",
        "NexusRaven-V2-13B",
        "Phind-CodeLlama-34B-v2",
        "CodeLlama-7b-Python-hf",
        "CodeLlama-7b-Python",
        "CodeLlama-13b-Python-hf",
        "CodeLlama-34b-Python-hf",
        "CodeLlama-70b-Python-hf",
        "snowflake-arctic-instruct",
        "SOLAR-10.7B-Instruct-v1.0",
        "StripedHyena-Hessian-7B",
        "StripedHyena-Nous-7B",
        "Llama-2-7B-32K-Instruct",
        "CodeLlama-13b-Instruct",
        "evo-1-131k-base",
        "OLMo-7B-Instruct",
        "Platypus2-70B-instruct",
        "Snorkel-Mistral-PairRM-DPO",
        "ReMM-SLERP-L2-13B",
        "MythoMax-L2-13b",
        "chronos-hermes-13b",
        "Llama-Guard-7b",
        "gemma-2-9b-it",
        "gemma-2-27b-it",
        "Toppy-M-7B",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "command-r+",
        "sparkdesk"
    ]

    def __init__(
        self,
        model: str = "gpt-4o", 
        max_tokens: int = 4096,
        temperature: float = 1,
        top_p: float = 1,
        is_conversation: bool = True,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        system_prompt: str = None,  
    ):
        """
        Initializes the DiscordRocks API with given parameters.

        Args:
            api_key (str): The API key for authentication.
            model (str): The AI model to use for text generation. Defaults to "llama-3-70b-chat".
            max_tokens (int): The maximum number of tokens to generate. Defaults to 4096.
            temperature (float): The temperature parameter for the model. Defaults to 1.
            top_p (float): The top_p parameter for the model. Defaults to 1.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            system_prompt (str, optional): System prompt to guide the AI's behavior. Defaults to None.
        """
        if model not in self.available_models:
            raise ValueError(f"Invalid model name. Available models are: {self.available_models}")


        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.chat_completions_url = "https://api.discord.rocks/chat/completions"
        self.images_generations_url = "https://api.discord.rocks/images/generations"
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://llmplayground.net",
            "priority": "u=1, i",
            "referer": "https://llmplayground.net/",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"
        }
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
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
        self.system_prompt = system_prompt  # Store the system prompt

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Dict[str, Any]:
        """
        Sends a prompt to the DiscordRocks AI API and returns the response.

        Args:
            prompt: The text prompt to generate text from.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            raw (bool, optional): Whether to return the raw response. Defaults to False.
            optimizer (str, optional): The name of the optimizer to use. Defaults to None.
            conversationally (bool, optional): Whether to chat conversationally. Defaults to False.

        Returns:
            The response from the API.
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
        
        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},  # Add system prompt
                {"role": "user", "content": conversation_prompt}
            ], 
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": stream
        }

        def for_stream():
            response = self.session.post(
                self.chat_completions_url, json=payload, headers=self.headers, stream=True, timeout=self.timeout
            )

            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason})"
                )
            streaming_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        json_line = json.loads(line.decode('utf-8').split('data: ')[1])
                        content = json_line['choices'][0]['delta']['content']
                        streaming_response += content
                        yield content if raw else dict(text=streaming_response)
                    except:
                        continue
            self.last_response.update(dict(text=streaming_response))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            response = self.session.post(
                self.chat_completions_url, json=payload, headers=self.headers, timeout=self.timeout
            )

            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason})"
                )
            response_data = response.json()
            full_content = ''.join([choice['message']['content'] for choice in response_data['choices']])
            self.last_response.update(dict(text=full_content))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            return self.last_response

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

    def generate_image(
        self,
        prompt: str,
        model: str = "dall-e-3",
        n: int = 1,
        quality: str = "hd",
        response_format: str = "url", 
        size: str = "1024x1024",
    ) -> dict:
        """
        Generates an image using the DiscordRocks API.

        Args:
            prompt (str): The prompt describing the image to generate.
            model (str, optional): The image generation model to use. Defaults to "dall-e-3".
            n (int, optional): The number of images to generate. Defaults to 1.
            quality (str, optional): The quality of the generated images ("standard", "hd"). Defaults to "hd".
            response_format (str, optional): The response format ("url", "b64_json"). Defaults to "url".
            size (str, optional): The size of the generated images ("256x256", "512x512", "1024x1024"). 
                                  Defaults to "1024x1024".

        Returns:
            dict: A dictionary containing the response from the API, including the generated image URLs.
        """
        payload = {
            "prompt": prompt,
            "model": model,
            "n": n,
            "quality": quality,
            "response format": response_format,
            "size": size
        }

        response = self.session.post(self.images_generations_url, headers=self.headers, json=payload)
        if not response.ok:
            raise exceptions.FailedToGenerateResponseError(
                f"Failed to generate image - ({response.status_code}, {response.reason})"
            )

        return response.json().get("data", [])
if __name__ == "__main__":
    from rich import print
    ai = DiscordRocks()
    response = ai.chat("tell me about india")
    for chunk in response:
        print(chunk, end="", flush=True)