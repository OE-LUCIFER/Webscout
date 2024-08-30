from typing import Any, AsyncGenerator, Dict, Optional, Callable, List

import httpx
import requests
import json

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions

class GROQ(Provider):
    """
    A class to interact with the GROQ AI API.
    """

    AVAILABLE_MODELS = [
        "llama-3.1-405b-reasoning",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-groq-70b-8192-tool-use-preview",
        "llama3-groq-8b-8192-tool-use-preview",
        "llama-guard-3-8b",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it",
        "gemma2-9b-it",
        "whisper-large-v3"
    ]

    def __init__(
        self,
        api_key: str,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 1,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1,
        model: str = "mixtral-8x7b-32768",
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        system_prompt: Optional[str] = None,
    ):
        """Instantiates GROQ

        Args:
            api_key (key): GROQ's API key.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 1.
            presence_penalty (int, optional): Chances of topic being repeated. Defaults to 0.
            frequency_penalty (int, optional): Chances of word being repeated. Defaults to 0.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 0.999.
            model (str, optional): LLM model name. Defaults to "mixtral-8x7b-32768".
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            system_prompt (str, optional): System prompt to guide the conversation. Defaults to None.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p
        self.chat_endpoint = "https://api.groq.com/openai/v1/chat/completions" 
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.available_functions: Dict[str, Callable] = {}  # Store available functions
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
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

    def add_function(self, function_name: str, function: Callable):
        """Add a function to the available functions dictionary.

        Args:
            function_name (str): The name of the function to be used in the prompt.
            function (Callable): The function itself.
        """
        self.available_functions[function_name] = function

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,  # Add tools parameter
    ) -> dict:
        """Chat with AI

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            tools (List[Dict[str, Any]], optional): List of tool definitions. See example in class docstring. Defaults to None.

        Returns:
           dict : {}
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

        messages = [{"content": conversation_prompt, "role": "user"}]
        if self.system_prompt:
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        self.session.headers.update(self.headers)
        payload = {
            "frequency_penalty": self.frequency_penalty,
            "messages": messages,
            "model": self.model,
            "presence_penalty": self.presence_penalty,
            "stream": stream,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "tools": tools  # Include tools in the payload
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            message_load = ""
            for value in response.iter_lines(
                decode_unicode=True,
                delimiter="" if raw else "data:",
                chunk_size=self.stream_chunk_size,
            ):
                try:
                    resp = json.loads(value)
                    incomplete_message = self.get_message(resp)
                    if incomplete_message:
                        message_load += incomplete_message
                        resp["choices"][0]["delta"]["content"] = message_load
                        self.last_response.update(resp)
                        yield value if raw else resp
                    elif raw:
                        yield value
                except json.decoder.JSONDecodeError:
                    pass

            # Handle tool calls if any
            if 'tool_calls' in self.last_response.get('choices', [{}])[0].get('message', {}):
                tool_calls = self.last_response['choices'][0]['message']['tool_calls']
                for tool_call in tool_calls:
                    function_name = tool_call.get('function', {}).get('name')
                    arguments = json.loads(tool_call.get('function', {}).get('arguments', "{}"))
                    if function_name in self.available_functions:
                        tool_response = self.available_functions[function_name](**arguments)
                        messages.append({
                            "tool_call_id": tool_call['id'],
                            "role": "tool",
                            "name": function_name,
                            "content": tool_response
                        })
                        payload['messages'] = messages
                        # Make a second call to get the final response
                        second_response = self.session.post(
                            self.chat_endpoint, json=payload, timeout=self.timeout
                        )
                        if second_response.ok:
                            self.last_response = second_response.json()
                        else:
                            raise exceptions.FailedToGenerateResponseError(
                                f"Failed to execute tool - {second_response.text}"
                            )

            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            response = self.session.post(
                self.chat_endpoint, json=payload, stream=False, timeout=self.timeout
            )
            if (
                not response.ok
                or not response.headers.get("Content-Type", "") == "application/json"
            ):
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )
            resp = response.json()

            # Handle tool calls if any
            if 'tool_calls' in resp.get('choices', [{}])[0].get('message', {}):
                tool_calls = resp['choices'][0]['message']['tool_calls']
                for tool_call in tool_calls:
                    function_name = tool_call.get('function', {}).get('name')
                    arguments = json.loads(tool_call.get('function', {}).get('arguments', "{}"))
                    if function_name in self.available_functions:
                        tool_response = self.available_functions[function_name](**arguments)
                        messages.append({
                            "tool_call_id": tool_call['id'],
                            "role": "tool",
                            "name": function_name,
                            "content": tool_response
                        })
                        payload['messages'] = messages
                        # Make a second call to get the final response
                        second_response = self.session.post(
                            self.chat_endpoint, json=payload, timeout=self.timeout
                        )
                        if second_response.ok:
                            resp = second_response.json()
                        else:
                            raise exceptions.FailedToGenerateResponseError(
                                f"Failed to execute tool - {second_response.text}"
                            )

            self.last_response.update(resp)
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            return resp

        return for_stream() if stream else for_non_stream()


    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            tools (List[Dict[str, Any]], optional): List of tool definitions. See example in class docstring. Defaults to None.
        Returns:
            str: Response generated
        """

        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally, tools=tools
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt,
                    False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                    tools=tools
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
        try:
            if response["choices"][0].get("delta"):
                return response["choices"][0]["delta"]["content"]
            return response["choices"][0]["message"]["content"]
        except KeyError:
            return ""


class AsyncGROQ(AsyncProvider):
    """
    An asynchronous class to interact with the GROQ AI API.
    """

    AVAILABLE_MODELS = [
        "llama-3.1-405b-reasoning",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-groq-70b-8192-tool-use-preview",
        "llama3-groq-8b-8192-tool-use-preview",
        "llama-guard-3-8b",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it",
        "gemma2-9b-it",
        "whisper-large-v3"
    ]

    def __init__(
        self,
        api_key: str,
        is_conversation: bool = True,
        max_tokens: int = 600,
        temperature: float = 1,
        presence_penalty: int = 0,
        frequency_penalty: int = 0,
        top_p: float = 1,
        model: str = "mixtral-8x7b-32768",
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        system_prompt: Optional[str] = None,
    ):
        """Instantiates AsyncGROQ

        Args:
            api_key (key): GROQ's API key.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            temperature (float, optional): Charge of the generated text's randomness. Defaults to 1.
            presence_penalty (int, optional): Chances of topic being repeated. Defaults to 0.
            frequency_penalty (int, optional): Chances of word being repeated. Defaults to 0.
            top_p (float, optional): Sampling threshold during inference time. Defaults to 0.999.
            model (str, optional): LLM model name. Defaults to "gpt-3.5-turbo".
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            system_prompt (str, optional): System prompt to guide the conversation. Defaults to None.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.top_p = top_p
        self.chat_endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.system_prompt = system_prompt
        self.available_functions: Dict[str, Callable] = {}  # Store available functions
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
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
        self.session = httpx.AsyncClient(headers=self.headers, proxies=proxies)

    def add_function(self, function_name: str, function: Callable):
        """Add a function to the available functions dictionary.

        Args:
            function_name (str): The name of the function to be used in the prompt.
            function (Callable): The function itself.
        """
        self.available_functions[function_name] = function

    async def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> dict | AsyncGenerator:
        """Chat with AI asynchronously.

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            tools (List[Dict[str, Any]], optional): List of tool definitions. See example in class docstring. Defaults to None.
        Returns:
           dict|AsyncGenerator : ai content
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

        messages = [{"content": conversation_prompt, "role": "user"}]
        if self.system_prompt:
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        payload = {
            "frequency_penalty": self.frequency_penalty,
            "messages": messages,
            "model": self.model,
            "presence_penalty": self.presence_penalty,
            "stream": stream,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "tools": tools
        }

        async def for_stream():
            async with self.session.stream(
                "POST", self.chat_endpoint, json=payload, timeout=self.timeout
            ) as response:
                if not response.is_success:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason_phrase})"
                    )

                message_load = ""
                intro_value = "data:"
                async for value in response.aiter_lines():
                    try:
                        if value.startswith(intro_value):
                            value = value[len(intro_value) :]
                        resp = json.loads(value)
                        incomplete_message = await self.get_message(resp)
                        if incomplete_message:
                            message_load += incomplete_message
                            resp["choices"][0]["delta"]["content"] = message_load
                            self.last_response.update(resp)
                            yield value if raw else resp
                        elif raw:
                            yield value
                    except json.decoder.JSONDecodeError:
                        pass

                # Handle tool calls if any (in streaming mode)
                if 'tool_calls' in self.last_response.get('choices', [{}])[0].get('message', {}):
                    tool_calls = self.last_response['choices'][0]['message']['tool_calls']
                    for tool_call in tool_calls:
                        function_name = tool_call.get('function', {}).get('name')
                        arguments = json.loads(tool_call.get('function', {}).get('arguments', "{}"))
                        if function_name in self.available_functions:
                            tool_response = self.available_functions[function_name](**arguments)
                            messages.append({
                                "tool_call_id": tool_call['id'],
                                "role": "tool",
                                "name": function_name,
                                "content": tool_response
                            })
                            payload['messages'] = messages
                            # Make a second call to get the final response
                            second_response = await self.session.post(
                                self.chat_endpoint, json=payload, timeout=self.timeout
                            )
                            if second_response.is_success:
                                self.last_response = second_response.json()
                            else:
                                raise exceptions.FailedToGenerateResponseError(
                                    f"Failed to execute tool - {second_response.text}"
                                )

            self.conversation.update_chat_history(
                prompt, await self.get_message(self.last_response)
            )

        async def for_non_stream():
            response = await self.session.post(
                self.chat_endpoint, json=payload, timeout=self.timeout
            )
            if not response.is_success:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason_phrase})"
                )
            resp = response.json()

            # Handle tool calls if any (in non-streaming mode)
            if 'tool_calls' in resp.get('choices', [{}])[0].get('message', {}):
                tool_calls = resp['choices'][0]['message']['tool_calls']
                for tool_call in tool_calls:
                    function_name = tool_call.get('function', {}).get('name')
                    arguments = json.loads(tool_call.get('function', {}).get('arguments', "{}"))
                    if function_name in self.available_functions:
                        tool_response = self.available_functions[function_name](**arguments)
                        messages.append({
                            "tool_call_id": tool_call['id'],
                            "role": "tool",
                            "name": function_name,
                            "content": tool_response
                        })
                        payload['messages'] = messages
                        # Make a second call to get the final response
                        second_response = await self.session.post(
                            self.chat_endpoint, json=payload, timeout=self.timeout
                        )
                        if second_response.is_success:
                            resp = second_response.json()
                        else:
                            raise exceptions.FailedToGenerateResponseError(
                                f"Failed to execute tool - {second_response.text}"
                            )

            self.last_response.update(resp)
            self.conversation.update_chat_history(
                prompt, await self.get_message(self.last_response)
            )
            return resp

        return for_stream() if stream else await for_non_stream()

    async def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str | AsyncGenerator:
        """Generate response `str` asynchronously.
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            tools (List[Dict[str, Any]], optional): List of tool definitions. See example in class docstring. Defaults to None.
        Returns:
            str|AsyncGenerator: Response generated
        """

        async def for_stream():
            async_ask = await self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally, tools=tools
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
                    tools=tools
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
        try:
            if response["choices"][0].get("delta"):
                return response["choices"][0]["delta"]["content"]
            return response["choices"][0]["message"]["content"]
        except KeyError:
            return ""