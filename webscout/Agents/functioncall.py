import json
import logging
from webscout import DeepInfra, WEBS

class FunctionCallingAgent:
    def __init__(self, model: str = "Qwen/Qwen2-72B-Instruct", 
                 system_prompt: str = 'You are a helpful assistant that will always answer what the user wants', 
                 tools: list = None):
        """
        Initialize the FunctionCallingAgent with the model, system prompt, and tools.

        Args:
            model (str): The model to use for deepinfra chat.
            system_prompt (str): The system prompt to initialize the model.
            tools (list): A list of tools the agent can use.
        """
        self.deepinfra = DeepInfra(model=model, system_prompt=system_prompt, timeout=300)
        self.tools = tools if tools is not None else []


    def function_call_handler(self, message_text: str) -> dict:
        """
        Handles function calls based on the provided message text.

        Args:
            message_text (str): The input message text from the user.

        Returns:
            dict: The extracted function call and arguments.
        """
        system_message = self._generate_system_message(message_text)
        response = self.deepinfra.chat(system_message)
        # logging.info(f"Raw response: {response}")

        return self._parse_function_call(response)

    def _generate_system_message(self, user_message: str) -> str:
        """
        Generates a system message incorporating the user message and available tools.

        Args:
            user_message (str): The input message from the user.

        Returns:
            str: The formatted system message.
        """
        tools_description = '\n'.join([f"{tool['function']['name']}: {tool['function'].get('description', '')}" for tool in self.tools])
        return (
            f"[SYSTEM] You are a helpful and capable AI assistant. "
            "Your goal is to understand the user's request and provide accurate and relevant information. "
            "You have access to the following tools:\n\n"
            f"{tools_description}\n\n"
            "To use a tool, please follow this format:\n\n"
            "```json\n"
            "{{ 'tool_name': 'tool_name', 'tool_input': {{ 'arg_1': 'value_1', 'arg_2': 'value_2', ... }} }}\n"
            "```\n\n"
            f"[USER] {user_message}"
        )

    def _parse_function_call(self, response: str) -> dict:
        """
        Parses the response from the model to extract the function call.

        Args:
            response (str): The raw response from the model.

        Returns:
            dict: A dictionary containing the function name and arguments.
        """
        try:
            # Find the JSON-like part of the response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No valid JSON structure found in the response.")

            response_json_str = response[start_idx:end_idx]

            # Replace single quotes with double quotes and remove extra braces
            response_json_str = response_json_str.replace("'", '"')
            response_json_str = response_json_str.replace("{{", "{").replace("}}", "}")
            
            # Remove any leading or trailing whitespace
            response_json_str = response_json_str.strip()

            # Attempt to load the JSON string
            return json.loads(response_json_str)

        except (ValueError, json.JSONDecodeError) as e:
            logging.error(f"Error parsing function call: {e}")
            return {"error": str(e)}

    def execute_function(self, function_call_data: dict) -> str:
        """
        Executes the specified function with the provided arguments.

        Args:
            function_call_data (dict): A dictionary containing the function name and arguments.

        Returns:
            str: The result of the function execution.
        """
        function_name = function_call_data.get("tool_name")  # Use 'tool_name' instead of 'name'
        arguments = function_call_data.get("tool_input", {})  # Use 'tool_input' instead of 'arguments'

        if not isinstance(arguments, dict):
            logging.error("Invalid arguments format.")
            return "Invalid arguments format."

        logging.info(f"Executing function: {function_name} with arguments: {arguments}")

        if function_name == "web_search":
            return self._handle_web_search(arguments)
        else:
            return f"Function '{function_name}' is not implemented."

    # def _handle_web_search(self, arguments: dict) -> str:
    #     """
    #     Handles web search queries using the WEBS tool.

    #     Args:
    #         arguments (dict): A dictionary containing the query argument.

    #     Returns:
    #         str: The result of the web search.
    #     """
    #     query = arguments.get("query")
    #     if not query:
    #         return "Please provide a search query."

    #     search_results = self.webs.text(query)
    #     # Additional processing of search results can be done here if needed.
    #     return f"Here's what I found:\n\n{search_results}"

# Example usage
if __name__ == "__main__":
    tools = [
        {
            "type": "function",
            "function": {
                "name": "UserDetail",
                "parameters": {
                    "type": "object",
                    "title": "UserDetail",
                    "properties": {
                        "name": {
                            "title": "Name",
                            "type": "string"
                        },
                        "age": {
                            "title": "Age",
                            "type": "integer"
                        }
                    },
                    "required": ["name", "age"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search query on google",
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
        }
    ]

    agent = FunctionCallingAgent(tools=tools)
    message = "websearch about helpingai-9b"
    function_call_data = agent.function_call_handler(message)
    print(f"Function Call Data: {function_call_data}")

    if "error" not in function_call_data:
        result = agent.execute_function(function_call_data)
        print(f"Function Execution Result: {result}")
