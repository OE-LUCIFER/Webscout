import requests
import json
from webscout.Local import Model, Thread, formats
from webscout.Local.utils import download_model
from webscout.Local.model import Model
from webscout.Local.thread import Thread
from webscout.Local import formats
from webscout.Local.samplers import SamplerSettings

from dotenv import load_dotenv; load_dotenv()
import os


# 1. Download the model

model_path = r'C:\Users\hp\Desktop\Webscout - Copy\jarvis-3b-q2_k.gguf'

# 2. Load the model 
# model = Model(model_path, n_gpu_layers=4)  
# 2. Define and register tools 

# --- Weather API Tool ---from webscout.Local import Model, Thread, formats
from webscout import DeepWEBS
from webscout.Local.utils import download_model
from webscout.Local.model import Model
from webscout.Local.thread import Thread
from webscout.Local import formats
from webscout.Local.samplers import SamplerSettings
def deepwebs_search(query, max_results=5):
    """Performs a web search using DeepWEBS and returns results as JSON."""
    deepwebs = DeepWEBS()
    search_config = DeepWEBS.DeepSearch(
        queries=[query],
        max_results=max_results,
        extract_webpage=False,
        safe=False,
        types=["web"],
        overwrite_query_html=True,
        overwrite_webpage_html=True,
    )
    search_results = deepwebs.queries_to_search_results(search_config)
    formatted_results = []
    for result in search_results[0]:  # Assuming only one query
        formatted_results.append(f"Title: {result['title']}\nURL: {result['url']}\n")
    return "\n".join(formatted_results)

# Load your model
# repo_id = "OEvortex/HelpingAI-9B" 
# filename = "helpingai-9b.Q4_0.gguf"
# model_path = download_model(repo_id, filename, token='')

# 2. Load the model 
model = Model(model_path, n_gpu_layers=10)

# Create a Thread
system_prompt = "You are a helpful AI assistant. Respond to user queries concisely. If a user asks for information that requires a web search, use the `deepwebs_search` tool. Do not call the tool if it is not necessary."
sampler = SamplerSettings(temp=0.7, top_p=0.9)  # Adjust these values as needed
# 4. Create a custom chatml format with your system prompt
custom_chatml = formats.chatml.copy()
custom_chatml['system_content'] = system_prompt
thread = Thread(model, custom_chatml, sampler=sampler)
# Add the deepwebs_search tool
thread.add_tool({
    "type": "function",
    "function": {
        "name": "deepwebs_search",
        "description": "Performs a web search using DeepWEBS and returns the title and URLs of the results.",
        "execute": deepwebs_search,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search on the web",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results (default: 5)",
                },
            },
            "required": ["query"],
        },
    },
})

# Start interacting with the model
while True:
    user_input = input("You: ")
    response = thread.send(user_input)
    print("Bot: ", response)  