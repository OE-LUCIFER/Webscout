
from rich import print
from webscout import YEPCHAT
def get_current_time():
    import datetime
    return f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}"
def get_weather(location: str) -> str:
    return f"The weather in {location} is sunny."


ai = YEPCHAT(Tools=True) # Set Tools=True to use tools in the chat.

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

response = ai.chat(input(">>> "))
for chunk in response:
    print(chunk, end="", flush=True)