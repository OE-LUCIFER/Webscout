import json
import logging
import time
from typing import Any, Dict, Optional

import requests
from webscout import WEBS  # Import only WEBS from webscout

class LLAMA3:

    AVAILABLE_MODELS = ["llama3-70b", "llama3-8b", "llama3-405b"]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        model: str = "llama3-8b",  
        system: str = "GPT syle",
        proxies: dict = {},  # Add proxies parameter
    ):
        """Instantiates Snova

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            model (str, optional): Snova model name. Defaults to "llama3-70b".
            system (str, optional): System prompt for Snova. Defaults to "Answer as concisely as possible.".
            proxies (dict, optional): Proxy settings for requests. Defaults to an empty dictionary.
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.model = model
        self.system = system
        self.last_response = {}
        self.env_type = "tp16405b" if "405b" in model else "tp16"
        self.headers = {'content-type': 'application/json'}
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

    def chat(self, prompt: str) -> str:
        data = {'body': {'messages': [{'role': 'system', 'content': self.system}, {'role': 'user', 'content': prompt}], 'stream': True, 'model': self.model}, 'env_type': self.env_type}
        response = self.session.post('https://fast.snova.ai/api/completion', headers=self.headers, json=data, stream=True, timeout=self.timeout)
        output = ''
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data:'):
                try:
                    data = json.loads(line[len('data: '):])
                    output += data.get("choices", [{}])[0].get("delta", {}).get("content", '')
                except json.JSONDecodeError:
                    if line[len('data: '):] == '[DONE]':
                        break
        return output

class FunctionCallingAgent:
    def __init__(self, model: str = "llama3-8b", 
                 system_prompt: str = 'You are a helpful assistant that will always answer what the user wants', 
                 tools: list = None):
        self.LLAMA3 = LLAMA3(model=model, system=system_prompt, timeout=300)
        self.tools = tools if tools is not None else []
        self.webs = WEBS()

    def function_call_handler(self, message_text: str) -> dict:
        system_message = self._generate_system_message(message_text)
        response = self.LLAMA3.chat(system_message)
        # logging.info(f"Raw response: {response}")
        return self._parse_function_call(response)

    def _generate_system_message(self, user_message: str) -> str:
        tools_description = '\n'.join([f"- {tool['function']['name']}: {tool['function'].get('description', '')}" for tool in self.tools])
        return (
            "You are an AI assistant capable of understanding user requests and using tools to fulfill them. "
            "Always respond using the JSON format specified below, even if you're not sure about the answer. "
            f"Available tools:\n{tools_description}\n\n"
            "Instructions:\n"
            "1. Analyze the user's request.\n"
            "2. Choose the most appropriate tool based on the request.\n"
            "3. Respond ONLY with a JSON object in this exact format:\n"
            "{\n"
            '  "tool_name": "name_of_the_tool",\n'
            '  "tool_input": {\n'
            '    "param1": "value1",\n'
            '    "param2": "value2"\n'
            "  }\n"
            "}\n\n"
            "If you can't determine a suitable tool, use the 'general_ai' tool with the user's message as the 'question' parameter.\n\n"
            f"User request: {user_message}\n\n"
            "Your response (in JSON format):"
        )

    def _parse_function_call(self, response: str) -> dict:
        try:
            # Find the JSON-like part of the response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No valid JSON structure found in the response.")

            response_json_str = response[start_idx:end_idx]
            
            # Attempt to load the JSON string
            return json.loads(response_json_str)

        except (ValueError, json.JSONDecodeError) as e:
            logging.error(f"Error parsing function call: {e}")
            return {"error": str(e)}

    def execute_function(self, function_call_data: dict) -> str:
        function_name = function_call_data.get("tool_name")
        arguments = function_call_data.get("tool_input", {})

        if not isinstance(arguments, dict):
            logging.error("Invalid arguments format.")
            return "Invalid arguments format."

        logging.info(f"Executing function: {function_name} with arguments: {arguments}")


# Example usage
if __name__ == "__main__":
    tools = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search query on Google",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "web search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "general_ai",
                "description": "Use AI to answer a general question",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to be answered by the AI"
                        }
                    },
                    "required": ["question"]
                }
            }
        }
    ]

    agent = FunctionCallingAgent(tools=tools)
    message = "open yt"
    function_call_data = agent.function_call_handler(message)
    print(f"Function Call Data: {function_call_data}")

    if "error" not in function_call_data:
        result = agent.execute_function(function_call_data)
        print(f"Function Execution Result: {result}")