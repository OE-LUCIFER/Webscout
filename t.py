from webscout.Local.utils import download_model
from webscout.Local.model import Model
from webscout.Local.thread import Thread
from webscout.Local import formats
# 1. Download the model
repo_id = "microsoft/Phi-3-mini-4k-instruct-gguf"  # Replace with the desired Hugging Face repo
filename = "Phi-3-mini-4k-instruct-q4.gguf" # Replace with the correct filename
model_path = download_model(repo_id, filename)

# 2. Load the model 
model = Model(model_path, n_gpu_layers=4)  

# 3. Create a Thread for conversation
thread = Thread(model, formats.phi3)

# 4. Start interacting with the model
thread.interact()