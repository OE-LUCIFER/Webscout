import time
import uuid
import cloudscraper
import json

from typing import Any, Dict, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import date

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import WEBS, exceptions


@dataclass
class ToolCall:
    tool_name: str
    tool_input: Dict[str, Any]


class YEPCHAT(Provider):
    AVAILABLE_MODELS = ["Mixtral-8x7B-Instruct-v0.1"]
    tool_call_start = "```tool_code"
    tool_call_end = "```"

    class ToolRegistry:
        def __init__(self):
            self.tools: Dict[str, Dict[str, Union[Callable, str, Dict]]] = {}

        def register_tool(
            self,
            name: str,
            function: Callable,
            description: str = "",
            parameters: Optional[Dict[str, Any]] = None,
        ):
            self.tools[name] = {
                "function": function,
                "description": description,
                "parameters": parameters,
            }

        def get_tool(self, name: str) -> Optional[Callable]:
            tool = self.tools.get(name)
            return tool["function"] if tool else None

        def get_tool_description(self, name: str) -> str:
            tool = self.tools.get(name)
            return tool["description"] if tool else ""

        def get_tool_parameters(self, name: str) -> Optional[Dict[str, Any]]:
            tool = self.tools.get(name)
            return tool["parameters"] if tool else None

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 1280,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "Mixtral-8x7B-Instruct-v0.1",
        temperature: float = 0.6,
        top_p: float = 0.7,
        Tools: bool = False,
        retries: int = 3,
        retry_delay: int = 5,
    ):
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}"
            )

        self.session = cloudscraper.create_scraper()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://api.yep.com/v1/chat/completions"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.use_tools = Tools
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json; charset=utf-8",
            "DNT": "1",
            "Origin": "https://yep.com",
            "Referer": "https://yep.com/",
            "Sec-CH-UA": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
        }
        self.cookies = {"__Host-session": uuid.uuid4().hex}

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method))
            and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(act, raise_not_found=True, default=None, case_insensitive=True)
            if act
            else intro or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.session.proxies = proxies

        self.tool_registry = self.ToolRegistry()
        self.knowledge_cutoff = "December 2023"
        self.retries = retries
        self.retry_delay = retry_delay

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        initial_response = None
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

        tool_call_data = None
        tool_output = None
        if self.use_tools:
            initial_response = self._get_initial_response(
                conversation_prompt, self.retries, self.retry_delay
            )
            # logging.info(f"Initial AI response: {initial_response}")

            tool_call_data = self._parse_function_call(initial_response)
            if tool_call_data and "error" not in tool_call_data:
                tool_call = ToolCall(**tool_call_data)
                tool_output = self.execute_tool(tool_call)
                # logging.info(f"Tool output: {tool_output}")

        final_response = self._get_final_response(
            prompt,
            initial_response,
            tool_call_data,
            tool_output,
            self.retries,
            self.retry_delay,
        )
        # logging.info(f"Final AI response: {final_response}")

        self.last_response.update(dict(text=final_response))
        self.conversation.update_chat_history(
            prompt, self.get_message(self.last_response)
        )
        return self.last_response

    def _get_initial_response(self, prompt: str, retries: int, retry_delay: int) -> str:
        for attempt in range(retries + 1):
            try:
                prompt = self._generate_system_message(prompt)
                data = {
                    "stream": False,
                    "max_tokens": self.max_tokens_to_sample,
                    "top_p": self.top_p,
                    "temperature": self.temperature,
                    "messages": [{"content": prompt, "role": "user"}],
                    "model": self.model,
                }

                response = self.session.post(
                    self.chat_endpoint,
                    headers=self.headers,
                    cookies=self.cookies,
                    json=data,
                    timeout=self.timeout,
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )
                return response.json()["choices"][0]["message"]["content"]
            except exceptions.FailedToGenerateResponseError as e:
                if attempt < retries:
                    # logging.warning(f"API request failed: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise e
            except Exception as e:
                if attempt < retries:
                    #  logging.warning(
                    #     f"An unexpected error occurred: {e}. Retrying in {retry_delay} seconds..."
                    # )
                    time.sleep(retry_delay)
                else:
                    raise e

    def _get_final_response(
        self,
        prompt: str,
        initial_response: str,
        tool_call_data: Optional[Dict],
        tool_output: Optional[str],
        retries: int,
        retry_delay: int,
    ) -> str:
        for attempt in range(retries + 1):
            try:
                data = {
                    "stream": False,
                    "max_tokens": self.max_tokens_to_sample,
                    "top_p": self.top_p,
                    "temperature": self.temperature,
                    "messages": [{"content": prompt, "role": "user"}],
                    "model": self.model,
                }

                if tool_output:
                    tool_call = ToolCall(**tool_call_data)
                    tool_description = self.tool_registry.get_tool_description(tool_call.tool_name)
                    final_prompt = (
                        f"I asked you to answer this question: '{prompt}'\n\n"
                        f"To assist in answering, you used the '{tool_call.tool_name}' tool, which {tool_description}\n"
                        f"The tool was called with these parameters: {json.dumps(tool_call.tool_input)}\n"
                        f"The tool provided this output:\n\n{tool_output}\n\n"
                        "Based on the original question and the tool's output, please provide a comprehensive and accurate answer. "
                        "Make sure to:\n"
                        "1. Directly address the user's question\n"
                        "2. Incorporate relevant information from the tool's output\n"
                        "3. Provide context or explanations where necessary\n"
                        "4. If the tool output doesn't fully answer the question, supplement with your general knowledge\n"
                        "5. If the tool output is an error message, acknowledge it and try to provide a helpful response based on your general knowledge\n\n"
                        "Your response:"
                    )
                    data["messages"][0]["content"] = final_prompt
                else:
                    data["messages"][0]["content"] = prompt

                response = self.session.post(
                    self.chat_endpoint,
                    headers=self.headers,
                    cookies=self.cookies,
                    json=data,
                    timeout=self.timeout,
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )
                return response.json()["choices"][0]["message"]["content"]
            except exceptions.FailedToGenerateResponseError as e:
                if attempt < retries:
                    # logging.warning(
                    #     f"API request failed: {e}. Retrying in {retry_delay} seconds..."
                    # )
                    time.sleep(retry_delay)
                else:
                    raise e
            except Exception as e:
                if attempt < retries:
                    # logging.warning(
                    #     f"An unexpected error occurred: {e}. Retrying in {retry_delay} seconds..."
                    # )
                    time.sleep(retry_delay)
                else:
                    raise e

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str:
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
        assert isinstance(response, dict)
        return response["text"]

    def _generate_system_message(self, user_message: str) -> str:
        tools_description = ""
        for name, tool_data in self.tool_registry.tools.items():
            description = tool_data["description"]
            parameters = tool_data.get("parameters")
            if parameters:
                params_str = ", ".join(
                    f"{param_name}: {param_desc['description']}"
                    for param_name, param_desc in parameters["properties"].items()
                )
                tools_description += f"- **{name}({params_str}):** {description}\n"
            else:
                tools_description += f"- **{name}()**: {description}\n"

        current_date = date.today().strftime("%B %d, %Y")
        return (
            f"Today's date is {current_date}. Your knowledge cutoff is {self.knowledge_cutoff}.\n"
            "You are a helpful AI assistant designed to assist users with their questions. "
            "You have access to a set of tools that can help you provide more accurate and informative answers. "
            f"Here is a list of the available tools and their functions:\n{tools_description}\n\n"
            "**Instructions:**\n"
            "1. Carefully analyze the user's request to understand their intent.\n"
            "2. Determine if any of the provided tools can be used to fulfill the request.\n"
            "3. If a tool can be used, choose the MOST APPROPRIATE tool. Don't choose a tool if it's not relevant to the request.\n"
            "4. If you decide to use a tool, provide your response ONLY in the following JSON format:\n"
            "   ```json\n"
            "   {{\n"
            '       "tool_name": "name_of_the_tool",\n'
            '       "tool_input": {{\n'
            '           "parameter1": "value1",\n'
            '           "parameter2": "value2"\n'
            '       }}\n'
            "   }}\n"
            "   ```\n"
            "   - Replace 'name_of_the_tool' with the actual name of the tool.\n"
            "   - Replace 'parameter1', 'parameter2', etc., with the actual parameters of the tool, along with their corresponding values.\n"
            "   - Do NOT include any explanations or additional text within the JSON response.\n"
            "5. If you determine that no tool is needed to answer the user's question, respond with the following JSON:\n"
            "   ```json\n"
            "   {{\n"
            '       "tool_name": "general_ai",\n'
            '       "tool_input": "None"\n'
            "   }}\n"
            "   ```\n"
            f"User Request: {user_message}\n"
            "Your Response (JSON only):"
        )

    def _parse_function_call(self, response: str) -> dict:
        try:
            parsed_response = json.loads(response)
            if isinstance(parsed_response, dict) and "tool_name" in parsed_response:
                # Ensure tool_input is a dictionary
                if "tool_input" not in parsed_response or not isinstance(parsed_response["tool_input"], dict):
                    parsed_response["tool_input"] = {"query": parsed_response.get("tool_input", "")}
                return parsed_response
        except json.JSONDecodeError:
            pass

        # If JSON parsing fails or doesn't contain expected structure, try to extract JSON from the response
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1
        if start_idx != -1 and end_idx != -1:
            try:
                parsed_response = json.loads(response[start_idx:end_idx])
                if "tool_name" in parsed_response:
                    # Ensure tool_input is a dictionary
                    if "tool_input" not in parsed_response or not isinstance(parsed_response["tool_input"], dict):
                        parsed_response["tool_input"] = {"query": parsed_response.get("tool_input", "")}
                    return parsed_response
            except json.JSONDecodeError:
                pass
        #         logging.error("Error parsing tool call: Invalid JSON structure.")
        
        # logging.error("Error parsing tool call: No valid JSON structure found.")
        return {"error": "No valid JSON structure found."}

    def _should_call_tool(self, response_text: str) -> bool:
        return any(
            tool_name.lower() in response_text.lower()
            for tool_name in self.tool_registry.tools
        )

    def execute_tool(self, tool_call: ToolCall) -> str:
        tool_name = tool_call.tool_name
        tool_input = tool_call.tool_input

        if tool_name == "general_ai":
            return tool_input

        tool_function = self.tool_registry.get_tool(tool_name)
        if tool_function:
            try:
                parameters = self.tool_registry.get_tool_parameters(tool_name)
                if parameters:
                    # If the tool expects parameters, pass them as keyword arguments
                    tool_output = tool_function(**tool_input)
                else:
                    # If the tool doesn't expect parameters, call it without arguments
                    tool_output = tool_function()
                return tool_output
            except Exception as e:
                # logging.error(f"Error executing tool {tool_name}: {e}")
                return f"Error executing tool {tool_name}: {e}"
        else:
            return f"Tool '{tool_name}' not found."


if __name__ == "__main__":
    from rich import print

    def get_current_time():
        """Returns the current time in HH:MM:SS format."""
        return time.strftime("%H:%M:%S")

    def get_weather(location: str) -> str:
        """
        Gets the current weather for a given location.

        Args:
            location (str): The location for which to retrieve the weather, 
                           such as a city and state, or a zip code.
                           Examples: "London, UK", "90210".

        Returns:
            str: A string describing the current weather in the specified location.
                 Note: This is a placeholder and should be replaced with an actual weather API call.
        """
        return f"The weather in {location} is sunny."

    def web_search(query: str) -> str:
        """
        Performs a web search and returns the top 3 results.

        Args:
            query (str): The search query to use.

        Returns:
            str: A formatted string containing the title, body, and URL of 
                 the top 3 search results. 
                 If no results are found, returns "No results found for your query."
        """
        webs = WEBS()
        results = webs.text(query, max_results=3)
        if results:
            formatted_results = "\n\n".join(
                f"**{i+1}. {result['title']}**\n{result['body']}\n[URL: {result['href']}]"
                for i, result in enumerate(results)
            )
            return formatted_results
        else:
            return "No results found for your query."

    ai = YEPCHAT(Tools=True)

    ai.tool_registry.register_tool("get_current_time", get_current_time, "Gets the current time.")
    ai.tool_registry.register_tool(
        "get_weather",
        get_weather,
        "Gets the weather for a given location.",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "The city and state, or zip code"}
            },
            "required": ["location"],
        },
    )
    ai.tool_registry.register_tool(
        "web_search",
        web_search,
        "Searches the web for information.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."}
            },
            "required": ["query"],
        },
    )

    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)