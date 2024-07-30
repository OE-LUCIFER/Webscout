import json
import logging
from webscout import DeepInfra, WEBS

class FunctionCallingAgent:
    def __init__(self, model: str = "Qwen/Qwen2-72B-Instruct", system_prompt: str = 'You are a helpful assistant that will always answer what user wants', tools: list = None):
        self.deepinfra = DeepInfra(model=model, system_prompt=system_prompt)
        self.tools = tools if tools is not None else []
        # logging.basicConfig(level=logging.INFO)
        # self.webs = WEBS()  # Initialize a WEBS object for web search

    def function_call_handler(self, message_text: str):
        """Handles function calls based on the provided message text

        Args:
            message_text (str): The input message text from the user.

        Returns:
            dict: The extracted function call and arguments.
        """
        system_message = f'[SYSTEM]You are a helpful assistant. You have access to the following functions: \n {str(self.tools)}\n\nTo use these functions respond with:\n<functioncall> {{ "name": "function_name", "arguments": {{ "arg_1": "value_1", "arg_2": "value_2", ... }} }}  </functioncall>  [USER] {message_text}'
        
        response = self.deepinfra.chat(system_message)
        # logging.info(f"Raw response: {response}")

        try:
            # Extract the JSON-like part of the response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx == -1 or end_idx == -1:
                raise ValueError("JSON-like structure not found in the response")

            response_json_str = response[start_idx:end_idx]
            # Ensure the JSON string is properly formatted
            response_json_str = response_json_str.replace("'", '"')  # Replace single quotes with double quotes
            response_json_str = response_json_str.strip()
            response_data = json.loads(response_json_str)
        except (ValueError, json.JSONDecodeError) as e:
            # logging.error(f"An error occurred while parsing response: {e}")
            return {"error": str(e)}

        return response_data

    def execute_function(self, function_call_data: dict) -> str:
        """Executes the specified function with the provided arguments.

        Args:
            function_call_data (dict): A dictionary containing the function name and arguments.

        Returns:
            str: The result of the function execution.
        """
        function_name = function_call_data.get("name")
        arguments = function_call_data.get("arguments", "{}")  # Default to empty dict if not present

        # Parse the arguments string into a dictionary
        try:
            arguments_dict = json.loads(arguments)
        except json.JSONDecodeError:
            # logging.error("Failed to parse arguments as JSON.")
            return "Invalid arguments format."

        # logging.info(f"Executing function: {function_name} with arguments: {arguments_dict}")

        # if function_name == "web_search":
        #     query = arguments_dict.get("query")
        #     if query:
        #         search_results = self.webs.text(query)
        #         # You can process the search results here, e.g., extract URLs, summarize, etc.
        #         return f"Here's what I found:\n\n{search_results}"
        #     else:
        #         return "Please provide a search query."
        # else:
        #     return f"Function '{function_name}' is not yet implemented."

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
    message = "tell me about HelpingAI flash"
    function_call_data = agent.function_call_handler(message)
    print(f"Function Call Data: {function_call_data}")

    if "error" not in function_call_data:
        result = agent.execute_function(function_call_data)
        # print(f"Function Execution Result: {result}")