# %pip install -U 'webscout[local]' -q 

from webscout.Local.utils import download_model
from webscout.Local.model import Model
from webscout.Local.thread import Thread
from webscout.Local import formats
from webscout.Local.samplers import SamplerSettings


# Download the model
repo_id = "Vortex4ai/Jarvis-0.5B" 
filename = "test2-q4_k_m.gguf"
model_path = download_model(repo_id, filename, token=None)

# Load the model
model = Model(model_path)

# Define the system prompt
system_prompt = "You are Jarvis a helpful AI that will always follow user"

# Create a chat format with your system prompt
jarvis = formats.chatml.copy()
jarvis['system_content'] = system_prompt

# Define your sampler settings (optional)
sampler = SamplerSettings(temp=0.7, top_p=0.9)

# Create a Thread with the custom format and sampler
thread = Thread(model, jarvis, sampler=sampler)

print(thread.send(input(">>> ")))

# ----------------------------or--------------------------------------

# Start interacting with the model
thread.interact(header="🌟 Welcome to Jarvis 0.5B demo 🚀", color=True)
# ----------------------------AUTOLLAMA--------------------------
from webscout import autollama

model_path = "Vortex4ai/Jarvis-0.5B"
gguf_file = "test2-q4_k_m.gguf"

autollama.main(model_path, gguf_file)  

# ----------------------------OLLAMA-----------------------------
from webscout import OLLAMA

ai = OLLAMA(model="test2-q4_k_m.gguf", system_prompt="You are Jarvis a helpful AI that will always follow the user")
response = ai.chat(input(">>> "), stream=True)
for chunk in response:
    print(chunk, end="", flush=True)

