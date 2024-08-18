import json
import logging
from webscout import LLAMA3, WEBS

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

    #     if function_name == "web_search":
    #         return self._handle_web_search(arguments)
    #     elif function_name == "general_ai":
    #         return self._handle_general_ai(arguments)
    #     else:
    #         return f"Function '{function_name}' is not implemented."

    # def _handle_web_search(self, arguments: dict) -> str:
    #     query = arguments.get("query")
    #     if not query:
    #         return "Please provide a search query."

    #     search_results = self.webs.text(query, max_results=3)
    #     formatted_results = "\n\n".join(
    #         f"{i+1}. {result['title']}\n{result['body']}\nURL: {result['href']}"
    #         for i, result in enumerate(search_results)
    #     )
    #     return f"Here's what I found:\n\n{formatted_results}"

    # def _handle_general_ai(self, arguments: dict) -> str:
    #     question = arguments.get("question")
    #     if not question:
    #         return "Please provide a question for the AI to answer."

    #     response = self.LLAMA3.chat(question)
    #     return response

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