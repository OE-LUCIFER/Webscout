from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from gpt4all import GPT4All
from gpt4all.gpt4all import empty_chat_session
from gpt4all.gpt4all import append_extension_if_missing


import logging

my_logger = logging.getLogger("gpt4all")
my_logger.setLevel(logging.CRITICAL)


class GPT4ALL(Provider):
    def __init__(
        self,
        model: str,
        is_conversation: bool = True,
        max_tokens: int = 800,
        temperature: float = 0.7,
        presence_penalty: int = 0,
        frequency_penalty: int = 1.18,
        top_p: float = 0.4,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        history_offset: int = 10250,
        act: str = None,
    ):
        """Instantiates GPT4ALL

        Args:
            model (str, optional): Path to LLM model (.gguf or .bin).
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 800.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 0.7.
            presence_penalty (int, optional): Chances of topic being repeated. Defaults to 0.
            frequency_penalty (int, optional): Chances of word being repeated. Defaults to 1.18.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 0.4.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p
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

        def get_model_name_path():
            import os
            from pathlib import Path

            initial_model_path = Path(append_extension_if_missing(model))
            if initial_model_path.exists:
                if not initial_model_path.is_absolute():
                    initial_model_path = Path(os.getcwd()) / initial_model_path
                return os.path.split(initial_model_path.as_posix())
            else:
                raise FileNotFoundError(
                    "File does not exist " + initial_model_path.as_posix()
                )

        model_dir, model_name = get_model_name_path()

        self.gpt4all = GPT4All(
            model_name=model_name,
            model_path=model_dir,
            allow_download=False,
            verbose=False,
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

        def for_stream():
            response = self.gpt4all.generate(
                prompt=conversation_prompt,
                max_tokens=self.max_tokens_to_sample,
                temp=self.temperature,
                top_p=self.top_p,
                repeat_penalty=self.frequency_penalty,
                streaming=True,
            )

            message_load: str = ""
            for token in response:
                message_load += token
                resp: dict = dict(text=message_load)
                yield token if raw else resp
                self.last_response.update(resp)

            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            self.gpt4all.current_chat_session = empty_chat_session()

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
            response (str): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]