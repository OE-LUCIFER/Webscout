from uuid import uuid4
from re import findall
import json


from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from typing import Any, AsyncGenerator, Dict

import cloudscraper


class YouChat(Provider):
    """
    This class provides methods for interacting with the You.com chat API in a consistent provider structure.
    """

    # Updated available models based on provided "aiModels" list
    AVAILABLE_MODELS = [
        # "gpt_4_5_preview", #isProOnly": true,
        # "openai_o3_mini_high", #isProOnly": true,
        # "openai_o3_mini_medium", #isProOnly": true,
        # "openai_o1", #isProOnly": true,
        # "openai_o1_preview", #isProOnly": true,
        # "openai_o1_mini", #isProOnly": true,
        "gpt_4o_mini",
        "gpt_4o",
        "gpt_4_turbo",
        # "gpt_4", #isProOnly": true,
        # "claude_3_7_sonnet_thinking", #isProOnly": true,
        # "claude_3_7_sonnet", #isProOnly": true,
        # "claude_3_5_sonnet", #isProOnly": true,
        # "claude_3_opus", #isProOnly": true,
        "claude_3_sonnet",
        "claude_3_5_haiku",
        # "qwq_32b", #isProOnly": true,
        "qwen2p5_72b",
        "qwen2p5_coder_32b",
        # "deepseek_r1", #isProOnly": true,
        # "deepseek_v3", #isProOnly": true,
        "grok_2",
        # "llama3_3_70b", #isProOnly": false, "isAllowedForUserChatModes": false,
        # "llama3_2_90b", #isProOnly": false, "isAllowedForUserChatModes": false,
        "llama3_1_405b",
        "mistral_large_2",
        "gemini_2_flash",
        "gemini_1_5_flash",
        "gemini_1_5_pro",
        "databricks_dbrx_instruct",
        "command_r_plus",
        "solar_1_mini",
        "dolphin_2_5"
    ]

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
        model: str = "gemini_2_flash",
    ):
        """Instantiates YouChat

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            model (str, optional): Model to use. Defaults to "claude_3_5_haiku".
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = cloudscraper.create_scraper()  # Create a Cloudscraper session
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://you.com/api/streamingSearch"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
            "Accept": "text/event-stream",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Referer": "https://you.com/search?q=hi&fromSearchBar=true&tbm=youchat",
            "Connection": "keep-alive",
            "DNT": "1",
        }
        self.cookies = {
            "uuid_guest_backup": uuid4().hex,
            "youchat_personalization": "true",
            "youchat_smart_learn": "true",
            "youpro_subscription": "false",
            "ydc_stytch_session": uuid4().hex,
            "ydc_stytch_session_jwt": uuid4().hex,
            "__cf_bm": uuid4().hex,
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

        trace_id = str(uuid4())
        conversation_turn_id = str(uuid4())
        
        # Updated query parameters to match the new API format
        params = {
            "page": 1,
            "count": 10,
            "safeSearch": "Moderate",
            "mkt": "en-IN",
            "enable_worklow_generation_ux": "true",
            "domain": "youchat",
            "use_personalization_extraction": "true",
            "queryTraceId": trace_id,
            "chatId": trace_id,
            "conversationTurnId": conversation_turn_id,
            "pastChatLength": 0,
            "selectedChatMode": "custom",
            "selectedAiModel": self.model,
            "enable_agent_clarification_questions": "true",
            "traceId": f"{trace_id}|{conversation_turn_id}|{uuid4()}",
            "use_nested_youchat_updates": "true"
        }
        
        # New payload format is JSON
        payload = {
            "query": conversation_prompt,
            "chat": "[]"
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, 
                headers=self.headers, 
                cookies=self.cookies, 
                params=params,
                data=json.dumps(payload),
                stream=True, 
                timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            streaming_text = ""
            found_marker = False  # Flag to track if we've passed the '####' marker
            
            for value in response.iter_lines(
                decode_unicode=True,
                chunk_size=self.stream_chunk_size,
                delimiter="\n",
            ):
                try:
                    if bool(value) and value.startswith('data: ') and 'youChatToken' in value:
                        data = json.loads(value[6:])
                        token = data.get('youChatToken', '')
                        
                        # Check if this is the marker with '####'
                        if token == '####':
                            found_marker = True
                            continue  # Skip the marker itself
                        
                        # Only process tokens after the marker has been found
                        if found_marker and token:
                            streaming_text += token
                            yield token if raw else dict(text=token)
                except json.decoder.JSONDecodeError:
                    pass

            self.last_response.update(dict(text=streaming_text))
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

            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

if __name__ == '__main__':
    from rich import print
    ai = YouChat(timeout=5000)
    response = ai.chat("hi", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
