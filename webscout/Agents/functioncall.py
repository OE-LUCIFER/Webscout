from datetime import date
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
import asyncio
import requests
from jinja2 import Template
from webscout import WEBS, ChatGPTES

@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = False

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, ToolParameter]
    function: Callable
    is_async: bool = False

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)
    
    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def to_schema(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            param.name: {
                                "type": param.type,
                                "description": param.description
                            } for param in tool.parameters.values()
                        },
                        "required": [
                            param.name for param in tool.parameters.values() 
                            if param.required
                        ]
                    }
                }
            }
            for tool in self._tools.values()
        ]

class FunctionCallingAgent:
    SYSTEM_TEMPLATE = Template("""You are an advanced AI assistant tasked with analyzing user requests and determining the most appropriate action. You have access to the following tools:

{{ tools_description }}

Instructions:
1. Carefully analyze the user's request.
2. Determine which tools (if any) are necessary to fulfill the request.
3. You can make multiple tool calls if needed to complete the task.
4. If you decide to use tool(s), respond ONLY with a JSON array in this format:
   [
     {
       "name": "tool_name",
       "arguments": {
         "param1": "value1",
         "param2": "value2"
       }
     },
     ... (more tool calls as needed)
   ]

5. If no tool is needed, respond with an empty array: []

The current date is {{ current_date }}. Your knowledge cutoff is {{ knowledge_cutoff }}.

User Request: {{ user_message }}

Your Response (JSON array only):""")

    def __init__(self, registry: ToolRegistry = None):
        self.ai = ChatGPTES(timeout=300, intro=None)
        self.registry = registry or ToolRegistry()
        self.knowledge_cutoff = "September 2022"
        self.logger = logging.getLogger(__name__)

    def _generate_system_message(self, user_message: str) -> str:
        tools_description = ""
        for tool in self.registry.list_tools():
            tools_description += f"- {tool.name}: {tool.description}\n"
            tools_description += "    Parameters:\n"
            for param in tool.parameters.values():
                tools_description += f"      - {param.name}: {param.description} ({param.type})\n"
        
        current_date = date.today().strftime("%B %d, %Y")
        return self.SYSTEM_TEMPLATE.render(
            tools_description=tools_description,
            current_date=current_date,
            knowledge_cutoff=self.knowledge_cutoff,
            user_message=user_message
        )

    async def _execute_tool(self, tool_call: Dict[str, Any]) -> Any:
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})

        tool = self.registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")

        try:
            if tool.is_async:
                return await tool.function(**arguments)
            else:
                return tool.function(**arguments)
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            raise

    async def process_request(self, message: str) -> List[Any]:
        """Process a user request and execute any necessary tool calls."""
        try:
            system_message = self._generate_system_message(message)
            response = self.ai.chat(system_message)
            self.logger.debug(f"Raw AI response: {response}")

            tool_calls = self._parse_tool_calls(response)
            if not tool_calls:
                return []

            results = []
            for tool_call in tool_calls:
                result = await self._execute_tool(tool_call)
                results.append(result)
            return results

        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}")
            raise

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Parse the AI response into a list of tool calls."""
        try:
            # Find the JSON array in the response
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1

            if start_idx == -1 or end_idx == -1:
                return []

            # Extract and parse the JSON array
            response_json = json.loads(response[start_idx:end_idx])
            
            if not isinstance(response_json, list):
                response_json = [response_json]
                
            return response_json

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Error parsing tool calls: {str(e)}")
            return []

# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and configure the tool registry
    registry = ToolRegistry()

    def web_search(query: str) -> str:
        # Implement actual web search logic
        return f"Search results for: {query}"

    def get_user_detail(name: str, age: int) -> Dict[str, Any]:
        return {"name": name, "age": age}

    # Register tools
    registry.register(Tool(
        name="web_search",
        description="Search the web for current information",
        parameters={
            "query": ToolParameter(
                name="query",
                type="string",
                description="The search query to execute",
                required=True
            )
        },
        function=web_search
    ))

    registry.register(Tool(
        name="get_user_detail",
        description="Get user details",
        parameters={
            "name": ToolParameter(
                name="name",
                type="string",
                description="User's name",
                required=True
            ),
            "age": ToolParameter(
                name="age",
                type="integer",
                description="User's age",
                required=True
            )
        },
        function=get_user_detail
    ))

    # Create agent
    agent = FunctionCallingAgent(registry=registry)

    # Test cases
    test_messages = [
        "What's the weather like in New York today?",
        "Get user details name as John and age as 30",
        "Search for latest news about AI",
    ]

    async def run_tests():
        for message in test_messages:
            print(f"\nProcessing: {message}")
            try:
                results = await agent.process_request(message)
                print(f"Results: {results}")
            except Exception as e:
                print(f"Error: {str(e)}")

    # Run test cases
    asyncio.run(run_tests())