"""

>>> python -m webscout.Extra.gguf convert -m "OEvortex/HelpingAI-Lite-1.5T" -q "q4_k_m,q5_k_m"
>>> # With upload options:
>>> python -m webscout.Extra.gguf convert -m "your-model" -u "username" -t "token" -q "q4_k_m"

"""

import subprocess
import os 
import sys
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from webscout.zeroart import figlet_format
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from ..Litlogger import Logger, LogFormat
from ..swiftcli import CLI, option

# Initialize LitLogger with ocean vibes
logger = Logger(
    name="GGUFConverter",
    format=LogFormat.MODERN_EMOJI,

)

console = Console()

class ConversionError(Exception):
    """Custom exception for when things don't go as planned! ⚠️"""
    pass

class ModelConverter:
    """Handles the conversion of Hugging Face models to GGUF format."""
    
    VALID_METHODS = {
        "q2_k": "2-bit quantization",
        "q3_k_l": "3-bit quantization (large)",
        "q3_k_m": "3-bit quantization (medium)",
        "q3_k_s": "3-bit quantization (small)",
        "q4_0": "4-bit quantization (version 0)",
        "q4_1": "4-bit quantization (version 1)",
        "q4_k_m": "4-bit quantization (medium)",
        "q4_k_s": "4-bit quantization (small)",
        "q5_0": "5-bit quantization (version 0)",
        "q5_1": "5-bit quantization (version 1)",
        "q5_k_m": "5-bit quantization (medium)",
        "q5_k_s": "5-bit quantization (small)",
        "q6_k": "6-bit quantization",
        "q8_0": "8-bit quantization"
    }
    
    def __init__(self, model_id: str, username: Optional[str] = None, 
                 token: Optional[str] = None, quantization_methods: str = "q4_k_m,q5_k_m"):
        self.model_id = model_id
        self.username = username
        self.token = token
        self.quantization_methods = quantization_methods.split(',')
        self.model_name = model_id.split('/')[-1]
        self.workspace = Path(os.getcwd())
        
    def validate_inputs(self) -> None:
        """Validates all input parameters."""
        if not '/' in self.model_id:
            raise ValueError("Invalid model ID format. Expected format: 'organization/model-name'")
            
        invalid_methods = [m for m in self.quantization_methods if m not in self.VALID_METHODS]
        if invalid_methods:
            raise ValueError(
                f"Invalid quantization methods: {', '.join(invalid_methods)}.\n"
                f"Valid methods are: {', '.join(self.VALID_METHODS.keys())}"
            )
            
        if bool(self.username) != bool(self.token):
            raise ValueError("Both username and token must be provided for upload, or neither.")
    
    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """Check if all required dependencies are installed."""
        dependencies = {
            'git': 'Git version control',
            'pip3': 'Python package installer',
            'huggingface-cli': 'Hugging Face CLI',
            'nvcc': 'NVIDIA CUDA Compiler (optional)'
        }
        
        status = {}
        for cmd, desc in dependencies.items():
            status[cmd] = subprocess.run(['which', cmd], capture_output=True, text=True).returncode == 0
            
        return status
    
    def setup_llama_cpp(self) -> None:
        """Sets up and builds llama.cpp repository."""
        llama_path = self.workspace / "llama.cpp"
        
        with console.status("[bold green]Setting up llama.cpp...") as status:
            if not llama_path.exists():
                logger.info("Cloning llama.cpp repository...")
                subprocess.run(['git', 'clone', 'https://github.com/ggerganov/llama.cpp'], check=True)
            
            os.chdir(llama_path)
            logger.info("Installing requirements...")
            subprocess.run(['pip3', 'install', '-r', 'requirements.txt'], check=True)
            
            has_cuda = subprocess.run(['nvcc', '--version'], capture_output=True).returncode == 0
            
            logger.info("Building llama.cpp...")
            subprocess.run(['make', 'clean'], check=True)
            if has_cuda:
                status.update("[bold green]Building with CUDA support...")
                subprocess.run(['make', 'LLAMA_CUBLAS=1'], check=True)
            else:
                status.update("[bold yellow]Building without CUDA support...")
                subprocess.run(['make'], check=True)
            
            os.chdir(self.workspace)
    
    def display_config(self) -> None:
        """Displays the current configuration in a formatted table."""
        table = Table(title="Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Model ID", self.model_id)
        table.add_row("Model Name", self.model_name)
        table.add_row("Username", self.username or "Not provided")
        table.add_row("Token", "****" if self.token else "Not provided")
        table.add_row("Quantization Methods", "\n".join(
            f"{method} ({self.VALID_METHODS[method]})" 
            for method in self.quantization_methods
        ))
        
        console.print(Panel(table))
    
    def convert(self) -> None:
        """Performs the model conversion process."""
        try:
            # Display banner and configuration
            console.print(f"[bold green]{figlet_format('GGUF Converter')}")
            self.display_config()
            
            # Validate inputs
            self.validate_inputs()
            
            # Check dependencies
            deps = self.check_dependencies()
            missing = [name for name, installed in deps.items() if not installed and name != 'nvcc']
            if missing:
                raise ConversionError(f"Missing required dependencies: {', '.join(missing)}")
            
            # Setup llama.cpp
            self.setup_llama_cpp()
            
            # Create and execute conversion script
            script_path = self.workspace / "gguf.sh"
            if not script_path.exists():
                self._create_conversion_script(script_path)
            
            # Prepare command
            command = ["bash", str(script_path), "-m", self.model_id]
            if self.username and self.token:
                command.extend(["-u", self.username, "-t", self.token])
            command.extend(["-q", ",".join(self.quantization_methods)])
            
            # Execute conversion with progress tracking
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Converting model...", total=None)
                
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        progress.update(task, description=output.strip())
                        logger.info(output.strip())
                
                stderr = process.stderr.read()
                if stderr:
                    logger.warning(stderr)
                
                if process.returncode != 0:
                    raise ConversionError(f"Conversion failed with return code {process.returncode}")
                
                progress.update(task, completed=True)
            
            # Display success message
            console.print(Panel.fit(
                "[bold green]✓[/] Conversion completed successfully!\n\n"
                f"[cyan]Output files can be found in: {self.workspace / self.model_name}[/]",
                title="Success",
                border_style="green"
            ))
            
        except Exception as e:
            console.print(Panel.fit(
                f"[bold red]✗[/] {str(e)}",
                title="Error",
                border_style="red"
            ))
            raise
    
    def _create_conversion_script(self, script_path: Path) -> None:
        """Creates the conversion shell script."""
        script_content = """cat << "EOF"
Made with love in India
EOF

# Default values
MODEL_ID=""
USERNAME=""
TOKEN=""
QUANTIZATION_METHODS="q4_k_m,q5_k_m" # Default to "q4_k_m,q5_k_m" if not provided

# Display help/usage information
usage() {
  echo "Usage: $0 -m MODEL_ID [-u USERNAME] [-t TOKEN] [-q QUANTIZATION_METHODS]"
  echo
  echo "Options:"
  echo "  -m MODEL_ID                   Required: Set the HF model ID"
  echo "  -u USERNAME                   Optional: Set the username"
  echo "  -t TOKEN                      Optional: Set the token"
  echo "  -q QUANTIZATION_METHODS       Optional: Set the quantization methods (default: q4_k_m,q5_k_m)"
  echo "  -h                            Display this help and exit"
  echo
}

# Parse command-line options
while getopts ":m:u:t:q:h" opt; do
  case ${opt} in
    m )
      MODEL_ID=$OPTARG
      ;;
    u )
      USERNAME=$OPTARG
      ;;
    t )
      TOKEN=$OPTARG
      ;;
    q )
      QUANTIZATION_METHODS=$OPTARG
      ;;
    h )
      usage
      exit 0
      ;;
    \? )
      echo "Invalid Option: -$OPTARG" 1>&2
      usage
      exit 1
      ;;
    : )
      echo "Invalid Option: -$OPTARG requires an argument" 1>&2
      usage
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

# Ensure MODEL_ID is provided
if [ -z "$MODEL_ID" ]; then
    echo "Error: MODEL_ID is required."
    usage
    exit 1
fi

# # Echoing the arguments for checking
# echo "MODEL_ID: $MODEL_ID"
# echo "USERNAME: ${USERNAME:-'Not provided'}"
# echo "TOKEN: ${TOKEN:-'Not provided'}"
# echo "QUANTIZATION_METHODS: $QUANTIZATION_METHODS"

# Splitting string into an array for quantization methods, if provided
IFS=',' read -r -a QUANTIZATION_METHOD_ARRAY <<< "$QUANTIZATION_METHODS"
echo "Quantization Methods: ${QUANTIZATION_METHOD_ARRAY[@]}"

MODEL_NAME=$(echo "$MODEL_ID" | awk -F'/' '{print $NF}')


# ----------- llama.cpp setup block-----------
# Check if llama.cpp is already installed and skip the build step if it is
if [ ! -d "llama.cpp" ]; then
    echo "llama.cpp not found. Cloning and setting up..."
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp && git pull
    # Install required packages
    pip3 install -r requirements.txt
    # Build llama.cpp as it's freshly cloned
    if ! command -v nvcc &> /dev/null
    then
        echo "nvcc could not be found, building llama without LLAMA_CUBLAS"
        make clean && make
    else
        make clean && LLAMA_CUBLAS=1 make
    fi
    cd ..
else
    echo "llama.cpp found. Assuming it's already built and up to date."
    # Optionally, still update dependencies
    # cd llama.cpp && pip3 install -r requirements.txt && cd ..
fi
# ----------- llama.cpp setup block-----------



# Download model 
#todo : shall we put condition to check if model has been already downloaded? similar to autogguf?
echo "Downloading the model..."
huggingface-cli download "$MODEL_ID" --local-dir "./${MODEL_NAME}" --local-dir-use-symlinks False --revision main


# Convert to fp16
FP16="${MODEL_NAME}/${MODEL_NAME,,}.fp16.bin"
echo "Converting the model to fp16..."
python3 llama.cpp/convert_hf_to_gguf.py "$MODEL_NAME" --outtype f16 --outfile "$FP16"

# Quantize the model
echo "Quantizing the model..."
for METHOD in "${QUANTIZATION_METHOD_ARRAY[@]}"; do
    QTYPE="${MODEL_NAME}/${MODEL_NAME,,}.${METHOD^^}.gguf"
    ./llama.cpp/llama-quantize "$FP16" "$QTYPE" "$METHOD"
done


# Check if USERNAME and TOKEN are provided
if [[ -n "$USERNAME" && -n "$TOKEN" ]]; then

    # Login to Hugging Face
    echo "Logging in to Hugging Face..."
    huggingface-cli login --token "$TOKEN"


    # Uploading .gguf, .md files, and config.json
    echo "Uploading .gguf, .md files, and config.json..."


    # Define a temporary directory
    TEMP_DIR="./temp_upload_dir"

    # Create the temporary directory
    mkdir -p "${TEMP_DIR}"

    # Copy the specific files to the temporary directory
    find "./${MODEL_NAME}" -type f \( -name "*.gguf" -o -name "*.md" -o -name "config.json" \) -exec cp {} "${TEMP_DIR}/" \;

    # Upload the temporary directory to Hugging Face
    huggingface-cli upload "${USERNAME}/${MODEL_NAME}-GGUF" "${TEMP_DIR}" --private

    # Remove the temporary directory after upload
    rm -rf "${TEMP_DIR}"
    echo "Upload completed."
else
    echo "USERNAME and TOKEN must be provided for upload."
fi

echo "Script completed."
            """
        script_path.write_text(script_content)
        script_path.chmod(0o755)

# Initialize CLI with HAI vibes
app = CLI(
    name="gguf",
    help="Convert HuggingFace models to GGUF format with style! 🔥",
    version="1.0.0"
)

@app.command(name="convert")
@option("-m", "--model-id", help="The HuggingFace model ID (e.g., 'OEvortex/HelpingAI-Lite-1.5T')", required=True)
@option("-u", "--username", help="Your HuggingFace username for uploads", default=None)
@option("-t", "--token", help="Your HuggingFace API token for uploads", default=None)
@option("-q", "--quantization", help="Comma-separated quantization methods", default="q4_k_m,q5_k_m")
def convert_command(model_id: str, username: Optional[str] = None, 
                   token: Optional[str] = None, quantization: str = "q4_k_m,q5_k_m"):
    """
    Convert and quantize HuggingFace models to GGUF format! 🚀
    
    Args:
        model_id (str): Your model's HF ID (like 'OEvortex/HelpingAI-Lite-1.5T') 🎯
        username (str, optional): Your HF username for uploads 👤
        token (str, optional): Your HF API token 🔑
        quantization (str): Quantization methods (default: q4_k_m,q5_k_m) 🎮
        
    Example:
        >>> python -m webscout.Extra.gguf convert \\
        ...     -m "OEvortex/HelpingAI-Lite-1.5T" \\
        ...     -q "q4_k_m,q5_k_m"
    """
    try:
        converter = ModelConverter(
            model_id=model_id,
            username=username,
            token=token,
            quantization_methods=quantization
        )
        converter.convert()
    except (ConversionError, ValueError) as e:
        logger.error(f"Conversion failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

def main():
    """Fire up the GGUF converter! 🚀"""
    app.run()

if __name__ == "__main__":
    main()
