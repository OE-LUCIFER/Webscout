import os
import openai
import requests
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider

class LLAMA3(Provider):
    """
    A class to interact with the Sambanova API using the openai library.
    """

    AVAILABLE_MODELS = [
        "Meta-Llama-3.1-8B-Instruct",
        "Meta-Llama-3.1-70B-Instruct",
        "Meta-Llama-3.1-405B-Instruct"
    ]

    def __init__(
        self,
        api_key: str = None,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 1,
        top_p: float = 0.95,
        model: str = "Meta-Llama-3.1-8B-Instruct",
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        """
        Initializes the Sambanova API with the given parameters.

        Args:
            api_key (str, optional): Your Sambanova API key. If None, it will use the environment variable "SAMBANOVA_API_KEY". Defaults to None.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): The temperature parameter for the model. Defaults to 1.
            top_p (float, optional): The top_p parameter for the model. Defaults to 0.95.
            model (str, optional): The name of the Sambanova model to use. Defaults to "Meta-Llama-3.1-8B-Instruct".
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            system_prompt (str, optional): System instruction to guide the AI's behavior.
                                           Defaults to "You are a helpful and informative AI assistant.".
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.api_key = api_key or os.environ["SAMBANOVA_API_KEY"]
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.system_prompt = system_prompt  # Add this line to set the system_prompt attribute

        self.session = requests.Session()  # Not directly used for Gemini API calls, but can be used for other requests
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
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
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.session.proxies = proxies

        # Configure the Sambanova API
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://api.sambanova.ai/v1",
        )

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
            stream (bool, optional): Not used for Sambanova API. Defaults to False.
            raw (bool, optional): Not used for Sambanova API. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
           dict : {}
        ```json
        {
           "text" : "How may I assist you today?"
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

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            temperature=self.temperature,
            top_p=self.top_p
        )

        self.last_response.update(dict(text=response.choices[0].message.content))
        self.conversation.update_chat_history(
            prompt, self.get_message(self.last_response)
        )
        return self.last_response

    def chat(
        self,
        prompt: str,
        stream: bool = False,  # Streaming not supported by the current google-generativeai library
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
        """Generate response `str`

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Not used for Sambanova API. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
        """
        return self.get_message(
            self.ask(
                prompt,
                optimizer=optimizer,
                conversationally=conversationally,
            )
        )

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == "__main__":
    from rich import print
    ai = LLAMA3(api_key='7979b01c-c5ea-40df-9198-f45733fa2208')
    response = ai.chat(input(">>> "))
    for chunks in response:
        print(chunks, end="", flush=True)