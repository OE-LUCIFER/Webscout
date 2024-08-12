import json
import logging
from webscout import LLAMA3, WEBS
from webscout.Agents.functioncall import FunctionCallingAgent

# Define tools that the agent can use
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
    },
    {  # New general AI tool
        "type": "function",
        "function": {
            "name": "general_ai",
            "description": "Use general AI knowledge to answer the question",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to answer"
                    }
                },
                "required": ["question"]
            }
        }
    }
]

# Initialize the FunctionCallingAgent with the specified tools
agent = FunctionCallingAgent(tools=tools)
llama = LLAMA3()
from rich import print
# Input message from the user
user = input(">>> ")
message = user
function_call_data = agent.function_call_handler(message)
print(f"Function Call Data: {function_call_data}")

# Check for errors in the function call data
if "error" not in function_call_data:
    function_name = function_call_data.get("tool_name")  # Use 'tool_name' instead of 'name'
    if function_name == "web_search":
        arguments = function_call_data.get("tool_input", {})  # Get tool input arguments
        query = arguments.get("query")
        if query:
            with WEBS() as webs:
                search_results = webs.text(query, max_results=5) 
            prompt = (
                f"Based on the following search results:\n\n{search_results}\n\n"
                f"Question: {user}\n\n"
                "Please provide a comprehensive answer to the question based on the search results above. "
                "Include relevant webpage URLs in your answer when appropriate. "
                "If the search results don't contain relevant information, please state that and provide the best answer you can based on your general knowledge."
            )
            response = llama.chat(prompt)
            for c in response:
                print(c, end="", flush=True)

        else:
            print("Please provide a search query.")
    elif function_name == "general_ai":  # Handle general AI tool
        arguments = function_call_data.get("tool_input", {})
        question = arguments.get("question")
        if question:
            response = llama.chat(question)  # Use LLM directly
            for c in response:
                print(c, end="", flush=True)
        else:
            print("Please provide a question.")
    else:
        result = agent.execute_function(function_call_data)
        print(f"Function Execution Result: {result}") 
else:
    print(f"Error: {function_call_data['error']}")
