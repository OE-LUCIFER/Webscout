import warnings
from datetime import time
import os
import sys
import subprocess
import logging
import psutil
from huggingface_hub import hf_hub_url, cached_download
import colorlog
import ollama  # Import ollama for interactive chat
import argparse  # Import argparse for command-line arguments

# Suppress specific warnings
warnings.filterwarnings(
    "ignore", category=FutureWarning, module="huggingface_hub.file_download"
)

# Configure logging with colors
handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
)

logger = colorlog.getLogger(__name__)
if not logger.hasHandlers():
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Redirect warnings to the logger but avoid duplication
logging.captureWarnings(True)
py_warnings_logger = logging.getLogger("py.warnings")
if not py_warnings_logger.hasHandlers():
    py_warnings_logger.addHandler(handler)


def show_art():
    logger.info("Made with love in India")


def usage():
    logger.info("Usage: python script.py -m <model_path> -g <gguf_file>")
    logger.info("Options:")
    logger.info("  -m <model_path>    Set the path to the model")
    logger.info("  -g <gguf_file>     Set the GGUF file name")
    logger.info("  -h                 Display this help and exit")


def is_model_downloaded(logging_name, download_log):
    if not os.path.exists(download_log):
        return False
    with open(download_log, "r") as f:
        for line in f:
            if line.strip() == logging_name:
                return True
    return False


def log_downloaded_model(logging_name, download_log):
    with open(download_log, "a") as f:
        f.write(logging_name + "\n")


def is_model_created(model_name):
    result = subprocess.run(["ollama", "list"], stdout=subprocess.PIPE)
    return model_name in result.stdout.decode("utf-8")


def download_model(repo_id, filename, token, cache_dir="downloads"):
    url = hf_hub_url(repo_id, filename)
    filepath = cached_download(
        url, cache_dir=cache_dir, force_filename=filename, use_auth_token=token
    )
    return filepath


def is_ollama_running():
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] in ["ollama", "ollama.exe"]:
            return True
    return False


def main(model_path=None, gguf_file=None):  # Modified to handle both CLI and non-CLI
    show_art()

    # Parse command-line arguments if provided
    parser = argparse.ArgumentParser(description="Download and create an Ollama model")
    parser.add_argument("-m", "--model_path", help="Path to the model on Hugging Face Hub")
    parser.add_argument("-g", "--gguf_file", help="Name of the GGUF file")
    args = parser.parse_args()

    # Use arguments from command line or function parameters
    model_path = args.model_path if args.model_path else model_path
    gguf_file = args.gguf_file if args.gguf_file else gguf_file

    if not model_path or not gguf_file:
        logger.error("Error: model_path and gguf_file are required.")
        usage()
        sys.exit(2)

    model_name = gguf_file.split(".Q4")[0]
    download_log = "downloaded_models.log"
    logging_name = f"{model_path}_{model_name}"

    # Ensure the log file exists
    if not os.path.exists(download_log):
        with open(download_log, 'w') as f:
            pass

    # Check if huggingface-hub is installed, and install it if not
    try:
        subprocess.check_output(['pip', 'show', 'huggingface-hub'])
    except subprocess.CalledProcessError:
        logger.info("Installing huggingface-hub...")
        subprocess.check_call(['pip', 'install', '-U', 'huggingface_hub[cli]'])
    else:
        logger.info("huggingface-hub is already installed.")

    # Check if the model has already been downloaded
    if is_model_downloaded(logging_name, download_log):
        logger.info(f"Model {logging_name} has already been downloaded. Skipping download.")
    else:
        logger.info(f"Downloading model {logging_name}...")
        token = os.getenv('HUGGINGFACE_TOKEN', None)
        if not token:
            logger.warning("Warning: HUGGINGFACE_TOKEN environment variable is not set. Using None.")
            token = None

        filepath = download_model(model_path, gguf_file, token)
        log_downloaded_model(logging_name, download_log)
        logger.info(f"Model {logging_name} downloaded and logged.")

    # Check if Ollama is installed, and install it if not
    try:
        subprocess.check_output(['ollama', '--version'])
    except subprocess.CalledProcessError:
        logger.info("Installing Ollama...")
        subprocess.check_call(['curl', '-fsSL', 'https://ollama.com/install.sh', '|', 'sh'])
    else:
        logger.info("Ollama is already installed.")

    # Check if Ollama is already running
    if is_ollama_running():
        logger.info("Ollama is already running. Skipping the start.")
    else:
        logger.info("Starting Ollama...")
        subprocess.Popen(['ollama', 'serve'])

        while not is_ollama_running():
            logger.info("Waiting for Ollama to start...")
            time.sleep(1)

        logger.info("Ollama has started.")

    # Check if the model has already been created
    if is_model_created(model_name):
        logger.info(f"Model {model_name} is already created. Skipping creation.")
    else:
        logger.info(f"Creating model {model_name}...")
        with open('Modelfile', 'w') as f:
            f.write(f"FROM ./downloads/{gguf_file}")
        subprocess.check_call(['ollama', 'create', model_name, '-f', 'Modelfile'])
        logger.info(f"Model {model_name} created.")

    logger.info(f"model name is > {model_name}")
    logger.info(f"Use Ollama run {model_name}")

if __name__ == "__main__":
    main()