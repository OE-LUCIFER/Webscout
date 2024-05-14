from webscout.Local.utils import download_model
from webscout.Local.model import Model
from webscout.Local.thread import Thread
from webscout.Local.formats import chatml_alpaca

# 1. Download the model
repo_id = "Qwen/Qwen1.5-0.5B-Chat-GGUF"  # Replace with the desired Hugging Face repo
filename = "qwen1_5-0_5b-chat-q4_k_m.gguf" # Replace with the correct filename
model_path = download_model(repo_id, filename)

# 2. Load the model 
model = Model(model_path, n_gpu_layers=4)  

# 3. Create a Thread for conversation
thread = Thread(model, chatml_alpaca)

# 4. Start interacting with the model
thread.interact()