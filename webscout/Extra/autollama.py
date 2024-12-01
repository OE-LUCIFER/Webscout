"""
Yo fam! 🔥 Welcome to AutoLlama - your go-to tool for downloading and setting up HelpingAI models! 💪

Created by the legendary Abhay Koul, this script's got your back when it comes to:
- Downloading models straight from HuggingFace Hub 🚀
- Setting up Ollama with zero hassle 💯
- Getting your AI assistant ready to vibe with you! ⚡

Usage:
>>> python -m webscout.Extra.autollama download -m "OEvortex/HelpingAI-Lite-1.5T" -g "HelpingAI-Lite-1.5T.q4_k_m.gguf"

Features:
- Smart model management 🧠
- Automatic dependency installation 📦
- Progress tracking that keeps it real 📈
- Error handling that's got your back 💪

Join the squad on Discord and level up your AI game! 🎮
"""

import warnings
from datetime import time
import os
import sys
import subprocess
import psutil
from huggingface_hub import hf_hub_download
from ..Litlogger import LitLogger, LogFormat, ColorScheme
from ..swiftcli import CLI, option
# import ollama

# Suppress specific warnings
warnings.filterwarnings(
    "ignore", category=FutureWarning, module="huggingface_hub.file_download"
)

# Initialize LitLogger with custom format and colors
logger = LitLogger(
    name="AutoLlama",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.OCEAN
)

def show_art():
    """Dropping that signature HAI love! 💝 Made with passion in India! 🇮🇳"""
    logger.info("Made with love in India")

def usage():
    logger.info("Usage: python script.py -m <model_path> -g <gguf_file>")
    logger.info("Options:")
    logger.info("  -m <model_path>    Set the path to the model")
    logger.info("  -g <gguf_file>     Set the GGUF file name")
    logger.info("  -h                 Display this help and exit")

def is_model_downloaded(logging_name, download_log):
    """
    Checking if we already got that model downloaded! 🔍
    
    Args:
        logging_name (str): The model's unique name in our records 📝
        download_log (str): Where we keep track of our downloads 📋
        
    Returns:
        bool: True if we got it, False if we need to grab it! 💯
    """
    if not os.path.exists(download_log):
        return False
    with open(download_log, "r") as f:
        for line in f:
            if line.strip() == logging_name:
                return True
    return False

def log_downloaded_model(logging_name, download_log):
    """
    Keeping track of our downloaded models like a boss! 📝
    
    Args:
        logging_name (str): Model's name to remember 🏷️
        download_log (str): Our download history file 📋
    """
    with open(download_log, "a") as f:
        f.write(logging_name + "\n")

def is_model_created(model_name):
    """
    Checking if the model's already set up in Ollama! 🔍
    
    Args:
        model_name (str): Name of the model we're looking for 🎯
        
    Returns:
        bool: True if it's ready to roll, False if we need to set it up! 💪
    """
    result = subprocess.run(["ollama", "list"], stdout=subprocess.PIPE)
    return model_name in result.stdout.decode("utf-8")

def download_model(repo_id, filename, token, cache_dir="downloads"):
    """
    Pulling models straight from HuggingFace Hub! 🚀
    
    Args:
        repo_id (str): Where to find the model on HF 🎯
        filename (str): Name of the file we want 📄
        token (str): Your HF access token (optional but recommended) 🔑
        cache_dir (str): Where to save the downloads (default: 'downloads') 📂
        
    Returns:
        str: Path to your downloaded model file 📍
        
    Raises:
        Exception: If something goes wrong, we'll let you know what's up! ⚠️
    """
    try:
        os.makedirs(cache_dir, exist_ok=True)
        
        # Download using hf_hub_download
        filepath = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            token=token,
            cache_dir=cache_dir,
            resume_download=True,
            force_download=False,
            local_files_only=False
        )
        
        # Ensure file is in the expected location
        expected_path = os.path.join(cache_dir, filename)
        if filepath != expected_path:
            os.makedirs(os.path.dirname(expected_path), exist_ok=True)
            if not os.path.exists(expected_path):
                import shutil
                shutil.copy2(filepath, expected_path)
            filepath = expected_path
            
        return filepath
    
    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        raise

def is_ollama_running():
    """
    Checking if Ollama's up and running! 🏃‍♂️
    
    Returns:
        bool: True if Ollama's vibing, False if it needs a kickstart! ⚡
    """
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] in ["ollama", "ollama.exe"]:
            return True
    return False

# Initialize CLI
app = CLI(
    name="autollama",
    help="Download and create Ollama models",
    version="1.0.0"
)

@app.command(name="download")
@option("-m", "--model-path", help="Path to the model on Hugging Face Hub", required=True)
@option("-g", "--gguf-file", help="Name of the GGUF file", required=True)
def download_command(model_path: str, gguf_file: str):
    """
    Your one-stop command to download and set up HelpingAI models! 🚀
    
    Args:
        model_path (str): Where to find your model on HuggingFace Hub 🎯
        gguf_file (str): The GGUF file you want to download 📄
        
    Example:
        >>> python -m webscout.Extra.autollama download \\
        ...     -m "OEvortex/HelpingAI-Lite-1.5T" \\
        ...     -g "HelpingAI-Lite-1.5T.q4_k_m.gguf"
    """
    show_art()

    model_name = gguf_file.split(".Q4")[0]
    download_log = "downloaded_models.log"
    logging_name = f"{model_path}_{model_name}"

    if not os.path.exists(download_log):
        with open(download_log, 'w') as f:
            pass

    try:
        subprocess.check_output(['pip', 'show', 'huggingface-hub'])
    except subprocess.CalledProcessError:
        logger.info("Installing huggingface-hub...")
        subprocess.check_call(['pip', 'install', '-U', 'huggingface_hub[cli]'])
    else:
        logger.info("huggingface-hub is already installed.")

    if is_model_downloaded(logging_name, download_log):
        logger.info(f"Model {logging_name} has already been downloaded. Skipping download.")
    else:
        logger.info(f"Downloading model {logging_name}...")
        token = os.getenv('HUGGINGFACE_TOKEN', None)
        if not token:
            logger.warning("Warning: HUGGINGFACE_TOKEN environment variable is not set. Using None.")
        
        filepath = download_model(model_path, gguf_file, token)
        log_downloaded_model(logging_name, download_log)
        logger.info(f"Model {logging_name} downloaded and logged.")

    try:
        subprocess.check_output(['ollama', '--version'])
    except subprocess.CalledProcessError:
        logger.info("Installing Ollama...")
        subprocess.check_call(['curl', '-fsSL', 'https://ollama.com/install.sh', '|', 'sh'])
    else:
        logger.info("Ollama is already installed.")

    if is_ollama_running():
        logger.info("Ollama is already running. Skipping the start.")
    else:
        logger.info("Starting Ollama...")
        subprocess.Popen(['ollama', 'serve'])

        while not is_ollama_running():
            logger.info("Waiting for Ollama to start...")
            time.sleep(1)

        logger.info("Ollama has started.")

    if is_model_created(model_name):
        logger.info(f"Model {model_name} is already created. Skipping creation.")
    else:
        logger.info(f"Creating model {model_name}...")
        with open('Modelfile', 'w') as f:
            f.write(f"FROM ./downloads/{gguf_file}")
        subprocess.check_call(['ollama', 'create', model_name, '-f', 'Modelfile'])
        logger.info(f"Model {model_name} created.")

    logger.success(f"model name is > {model_name}")
    logger.info(f"Use Ollama run {model_name}")

def main():
    """
    Main function to run the AutoLlama CLI.
    """
    app.run()

if __name__ == "__main__":
    main()