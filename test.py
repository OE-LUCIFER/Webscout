from webscout import gguf
"""
Valid quantization methods:
"q2_k", "q3_k_l", "q3_k_m", "q3_k_s", 
"q4_0", "q4_1", "q4_k_m", "q4_k_s", 
"q5_0", "q5_1", "q5_k_m", "q5_k_s", 
"q6_k", "q8_0"
"""
gguf.convert(
    model_id="OEvortex/HelpingAI-Lite-1.5T",  # Replace with your model ID
    username="Abhaykoul",  # Replace with your Hugging Face username
    token="hf_token_write",  # Replace with your Hugging Face token
    quantization_methods="q4_k_m"  # Optional, adjust quantization methods
)

# ---------------------------------------------------------------------Autollama---------------------------------------------------------------------
from webscout import autollama

autollama(
    model_path="OEvortex/HelpingAI-Lite-1.5T-GGUF",
    gguf_file="model_name.gguf"
)
# python -m webscout.Extra.gguf -m "OEvortex/HelpingAI-Lite-1.5T" -u "your_username" -t "your_hf_token" -q "q4_k_m,q5_k_m" 
# python -m webscout.Extra.autollama -m "path/to/model" -g "model_name.gguf" 
