"""
Convert Hugging Face models to GGUF format with advanced features.

>>> python -m webscout.Extra.gguf convert -m "OEvortex/HelpingAI-Lite-1.5T" -q "q4_k_m,q5_k_m"
>>> # With upload options:
>>> python -m webscout.Extra.gguf convert -m "your-model" -u "username" -t "token" -q "q4_k_m"
>>> # With imatrix quantization:
>>> python -m webscout.Extra.gguf convert -m "your-model" -i -q "iq4_nl" -t "train_data.txt"
>>> # With model splitting:
>>> python -m webscout.Extra.gguf convert -m "your-model" -s --split-max-tensors 256
"""

import subprocess
import os 
import sys
import signal
import tempfile
import platform
from pathlib import Path
from typing import Optional, Dict, List, Any, Union, Literal, TypedDict, Set

from huggingface_hub import HfApi
from webscout.zeroart import figlet_format
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ..swiftcli import CLI, option

console = Console()

class ConversionError(Exception):
    """Custom exception for when things don't go as planned! ⚠️"""
    pass

class QuantizationMethod(TypedDict):
    """Type definition for quantization method descriptions."""
    description: str

class ModelConverter:
    """Handles the conversion of Hugging Face models to GGUF format."""
    
    VALID_METHODS: Dict[str, str] = {
        "fp16": "16-bit floating point - maximum accuracy, largest size",
        "q2_k": "2-bit quantization (smallest size, lowest accuracy)",
        "q3_k_l": "3-bit quantization (large) - balanced for size/accuracy",
        "q3_k_m": "3-bit quantization (medium) - good balance for most use cases",
        "q3_k_s": "3-bit quantization (small) - optimized for speed",
        "q4_0": "4-bit quantization (version 0) - standard 4-bit compression",
        "q4_1": "4-bit quantization (version 1) - improved accuracy over q4_0",
        "q4_k_m": "4-bit quantization (medium) - balanced for most models",
        "q4_k_s": "4-bit quantization (small) - optimized for speed",
        "q5_0": "5-bit quantization (version 0) - high accuracy, larger size",
        "q5_1": "5-bit quantization (version 1) - improved accuracy over q5_0",
        "q5_k_m": "5-bit quantization (medium) - best balance for quality/size",
        "q5_k_s": "5-bit quantization (small) - optimized for speed",
        "q6_k": "6-bit quantization - highest accuracy, largest size",
        "q8_0": "8-bit quantization - maximum accuracy, largest size"
    }
    
    VALID_IMATRIX_METHODS: Dict[str, str] = {
        "iq3_m": "3-bit imatrix quantization (medium) - balanced importance-based",
        "iq3_xxs": "3-bit imatrix quantization (extra extra small) - maximum compression",
        "q4_k_m": "4-bit imatrix quantization (medium) - balanced importance-based",
        "q4_k_s": "4-bit imatrix quantization (small) - optimized for speed",
        "iq4_nl": "4-bit imatrix quantization (non-linear) - best accuracy for 4-bit",
        "iq4_xs": "4-bit imatrix quantization (extra small) - maximum compression",
        "q5_k_m": "5-bit imatrix quantization (medium) - balanced importance-based",
        "q5_k_s": "5-bit imatrix quantization (small) - optimized for speed"
    }
    
    def __init__(
        self,
        model_id: str,
        username: Optional[str] = None,
        token: Optional[str] = None,
        quantization_methods: str = "q4_k_m",
        use_imatrix: bool = False,
        train_data_file: Optional[str] = None,
        split_model: bool = False,
        split_max_tensors: int = 256,
        split_max_size: Optional[str] = None
    ) -> None:
        self.model_id = model_id
        self.username = username
        self.token = token
        self.quantization_methods = quantization_methods.split(',')
        self.model_name = model_id.split('/')[-1]
        self.workspace = Path(os.getcwd())
        self.use_imatrix = use_imatrix
        self.train_data_file = train_data_file
        self.split_model = split_model
        self.split_max_tensors = split_max_tensors
        self.split_max_size = split_max_size
        self.fp16_only = "fp16" in self.quantization_methods and len(self.quantization_methods) == 1
        
    def validate_inputs(self) -> None:
        """Validates all input parameters."""
        if not '/' in self.model_id:
            raise ValueError("Invalid model ID format. Expected format: 'organization/model-name'")
            
        if self.use_imatrix:
            invalid_methods = [m for m in self.quantization_methods if m not in self.VALID_IMATRIX_METHODS]
            if invalid_methods:
                raise ValueError(
                    f"Invalid imatrix quantization methods: {', '.join(invalid_methods)}.\n"
                    f"Valid methods are: {', '.join(self.VALID_IMATRIX_METHODS.keys())}"
                )
            if not self.train_data_file and not os.path.exists("llama.cpp/groups_merged.txt"):
                raise ValueError("Training data file is required for imatrix quantization")
        else:
            invalid_methods = [m for m in self.quantization_methods if m not in self.VALID_METHODS]
            if invalid_methods:
                raise ValueError(
                    f"Invalid quantization methods: {', '.join(invalid_methods)}.\n"
                    f"Valid methods are: {', '.join(self.VALID_METHODS.keys())}"
                )
            
        if bool(self.username) != bool(self.token):
            raise ValueError("Both username and token must be provided for upload, or neither.")
            
        if self.split_model and self.split_max_size:
            try:
                size = int(self.split_max_size[:-1])
                unit = self.split_max_size[-1].upper()
                if unit not in ['M', 'G']:
                    raise ValueError("Split max size must end with M or G")
            except ValueError:
                raise ValueError("Invalid split max size format. Use format like '256M' or '5G'")
                
    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """Check if all required dependencies are installed."""
        dependencies: Dict[str, str] = {
            'git': 'Git version control',
            'pip3': 'Python package installer',
            'huggingface-cli': 'Hugging Face CLI',
            'cmake': 'CMake build system',
            'ninja': 'Ninja build system (optional)'
        }
        
        status: Dict[str, bool] = {}
        for cmd, desc in dependencies.items():
            status[cmd] = subprocess.run(['which', cmd], capture_output=True, text=True).returncode == 0
            
        return status
    
    def detect_hardware(self) -> Dict[str, bool]:
        """Detect available hardware acceleration."""
        hardware: Dict[str, bool] = {
            'cuda': False,
            'metal': False,
            'opencl': False,
            'vulkan': False,
            'rocm': False
        }
        
        # Check CUDA
        try:
            if subprocess.run(['nvcc', '--version'], capture_output=True).returncode == 0:
                hardware['cuda'] = True
        except FileNotFoundError:
            pass
            
        # Check Metal (macOS)
        if platform.system() == 'Darwin':
            try:
                if subprocess.run(['xcrun', '--show-sdk-path'], capture_output=True).returncode == 0:
                    hardware['metal'] = True
            except FileNotFoundError:
                pass
                
        # Check OpenCL
        try:
            if subprocess.run(['clinfo'], capture_output=True).returncode == 0:
                hardware['opencl'] = True
        except FileNotFoundError:
            pass
            
        # Check Vulkan
        try:
            if subprocess.run(['vulkaninfo'], capture_output=True).returncode == 0:
                hardware['vulkan'] = True
        except FileNotFoundError:
            pass
            
        # Check ROCm
        try:
            if subprocess.run(['rocm-smi'], capture_output=True).returncode == 0:
                hardware['rocm'] = True
        except FileNotFoundError:
            pass
            
        return hardware
    
    def setup_llama_cpp(self) -> None:
        """Sets up and builds llama.cpp repository."""
        llama_path = self.workspace / "llama.cpp"
        
        with console.status("[bold green]Setting up llama.cpp...") as status:
            # Clone llama.cpp if not exists
            if not llama_path.exists():
                subprocess.run(['git', 'clone', 'https://github.com/ggerganov/llama.cpp'], check=True)
            
            os.chdir(llama_path)
            
            # Check if we're in a Nix environment
            is_nix = platform.system() == "Linux" and os.path.exists("/nix/store")
            
            if is_nix:
                console.print("[yellow]Detected Nix environment. Using system Python packages...")
                # In Nix, we need to use the system Python packages
                try:
                    # Try to import required packages to check if they're available
                    import torch # type: ignore
                    import numpy # type: ignore 
                    import sentencepiece # type: ignore
                    import transformers # type: ignore
                    console.print("[green]Required Python packages are already installed.")
                except ImportError as e:
                    console.print("[red]Missing required Python packages in Nix environment.")
                    console.print("[yellow]Please install them using:")
                    console.print("nix-shell -p python3Packages.torch python3Packages.numpy python3Packages.sentencepiece python3Packages.transformers")
                    raise ConversionError("Missing required Python packages in Nix environment")
            else:
                # In non-Nix environments, install requirements
                try:
                    subprocess.run(['pip3', 'install', '-r', 'requirements.txt'], check=True)
                except subprocess.CalledProcessError as e:
                    if "externally-managed-environment" in str(e):
                        console.print("[yellow]Detected externally managed Python environment.")
                        console.print("[yellow]Please install the required packages manually:")
                        console.print("pip install torch numpy sentencepiece transformers")
                        raise ConversionError("Failed to install requirements in externally managed environment")
                    raise
            
            # Detect available hardware
            hardware = self.detect_hardware()
            console.print("[bold green]Detected hardware acceleration:")
            for hw, available in hardware.items():
                console.print(f"  {'✓' if available else '✗'} {hw.upper()}")
            
            # Configure CMake build
            cmake_args: List[str] = ['cmake', '-B', 'build']
            
            # Add hardware acceleration options
            if hardware['cuda']:
                cmake_args.extend(['-DLLAMA_CUBLAS=ON'])
            if hardware['metal']:
                cmake_args.extend(['-DLLAMA_METAL=ON'])
            if hardware['opencl']:
                cmake_args.extend(['-DLLAMA_CLBLAST=ON'])
            if hardware['vulkan']:
                cmake_args.extend(['-DLLAMA_VULKAN=ON'])
            if hardware['rocm']:
                cmake_args.extend(['-DLLAMA_HIPBLAS=ON'])
                
            # Use Ninja if available
            if subprocess.run(['which', 'ninja'], capture_output=True).returncode == 0:
                cmake_args.extend(['-G', 'Ninja'])
                
            # Configure the build
            subprocess.run(cmake_args, check=True)
            
            # Build the project
            if any(hardware.values()):
                status.update("[bold green]Building with hardware acceleration...")
            else:
                status.update("[bold yellow]Building for CPU only...")
                
            subprocess.run(['cmake', '--build', 'build', '-j', str(os.cpu_count() or 1)], check=True)
            
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
    
    def generate_importance_matrix(self, model_path: str, train_data_path: str, output_path: str) -> None:
        """Generates importance matrix for quantization."""
        imatrix_command: List[str] = [
            "./llama.cpp/build/bin/llama-imatrix",
            "-m", model_path,
            "-f", train_data_path,
            "-ngl", "99",
            "--output-frequency", "10",
            "-o", output_path,
        ]

        if not os.path.isfile(model_path):
            raise ConversionError(f"Model file not found: {model_path}")

        console.print("[bold green]Generating importance matrix...")
        process = subprocess.Popen(imatrix_command, shell=False)

        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            console.print("[yellow]Imatrix computation timed out. Sending SIGINT...")
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                console.print("[red]Imatrix process still running. Force terminating...")
                process.kill()

        if process.returncode != 0:
            raise ConversionError("Failed to generate importance matrix")

        console.print("[green]Importance matrix generation completed.")
    
    def split_model(self, model_path: str, outdir: str) -> List[str]:
        """Splits the model into smaller chunks."""
        split_cmd: List[str] = [
            "./llama.cpp/build/bin/llama-gguf-split",
            "--split",
        ]
        
        if self.split_max_size:
            split_cmd.extend(["--split-max-size", self.split_max_size])
        else:
            split_cmd.extend(["--split-max-tensors", str(self.split_max_tensors)])

        model_path_prefix = '.'.join(model_path.split('.')[:-1])
        split_cmd.extend([model_path, model_path_prefix])

        console.print(f"[bold green]Splitting model with command: {' '.join(split_cmd)}")
        
        result = subprocess.run(split_cmd, shell=False, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise ConversionError(f"Error splitting model: {result.stderr}")
            
        console.print("[green]Model split successfully!")
        
        # Get list of split files
        model_file_prefix = model_path_prefix.split('/')[-1]
        split_files = [f for f in os.listdir(outdir) 
                      if f.startswith(model_file_prefix) and f.endswith(".gguf")]
        
        if not split_files:
            raise ConversionError("No split files found")
            
        return split_files
    
    def upload_split_files(self, split_files: List[str], outdir: str, repo_id: str) -> None:
        """Uploads split model files to Hugging Face."""
        api = HfApi(token=self.token)
        
        for file in split_files:
            file_path = os.path.join(outdir, file)
            console.print(f"[bold green]Uploading file: {file}")
            try:
                api.upload_file(
                    path_or_fileobj=file_path,
                    path_in_repo=file,
                    repo_id=repo_id,
                )
            except Exception as e:
                raise ConversionError(f"Error uploading file {file}: {e}")
    
    def generate_readme(self, quantized_files: List[str]) -> str:
        """Generate a README.md file for the Hugging Face Hub."""
        readme = f"""# {self.model_name} GGUF

This repository contains GGUF quantized versions of [{self.model_id}](https://huggingface.co/{self.model_id}).

## About

This model was converted using [Webscout](https://github.com/Webscout/webscout).

## Quantization Methods

The following quantization methods were used:

"""
        # Add quantization method descriptions
        for method in self.quantization_methods:
            if self.use_imatrix:
                readme += f"- `{method}`: {self.VALID_IMATRIX_METHODS[method]}\n"
            else:
                readme += f"- `{method}`: {self.VALID_METHODS[method]}\n"

        readme += """
## Available Files

The following quantized files are available:

"""
        # Add file information
        for file in quantized_files:
            readme += f"- `{file}`\n"

        if self.use_imatrix:
            readme += """
## Importance Matrix

This model was quantized using importance matrix quantization. The `imatrix.dat` file contains the importance matrix used for quantization.

"""

        readme += """
## Usage

These GGUF files can be used with [llama.cpp](https://github.com/ggerganov/llama.cpp) and compatible tools.

Example usage:
```bash
./main -m model.gguf -n 1024 --repeat_penalty 1.0 --color -i -r "User:" -f prompts/chat-with-bob.txt
```

## Conversion Process

This model was converted using the following command:
```bash
python -m webscout.Extra.gguf convert \\
    -m "{self.model_id}" \\
    -q "{','.join(self.quantization_methods)}" \\
    {f'-i' if self.use_imatrix else ''} \\
    {f'--train-data "{self.train_data_file}"' if self.train_data_file else ''} \\
    {f'-s' if self.split_model else ''} \\
    {f'--split-max-tensors {self.split_max_tensors}' if self.split_model else ''} \\
    {f'--split-max-size {self.split_max_size}' if self.split_max_size else ''}
```

## License

This repository is licensed under the same terms as the original model.
"""
        return readme

    def upload_readme(self, readme_content: str, repo_id: str) -> None:
        """Upload README.md to Hugging Face Hub."""
        api = HfApi(token=self.token)
        try:
            api.upload_file(
                path_or_fileobj=readme_content.encode(),
                path_in_repo="README.md",
                repo_id=repo_id,
            )
            console.print("[green]README.md uploaded successfully!")
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to upload README.md: {e}")

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
            missing = [name for name, installed in deps.items() if not installed and name != 'ninja']
            if missing:
                raise ConversionError(f"Missing required dependencies: {', '.join(missing)}")
            
            # Setup llama.cpp
            self.setup_llama_cpp()
            
            # Determine if we need temporary directories (only for uploads)
            needs_temp = bool(self.username and self.token)
            
            if needs_temp:
                # Use temporary directories for upload case
                with tempfile.TemporaryDirectory() as outdir:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        self._convert_with_dirs(tmpdir, outdir)
            else:
                # Use current directory for local output
                outdir = os.getcwd()
                tmpdir = os.path.join(outdir, "temp_download")
                os.makedirs(tmpdir, exist_ok=True)
                try:
                    self._convert_with_dirs(tmpdir, outdir)
                finally:
                    # Clean up temporary download directory
                    import shutil
                    shutil.rmtree(tmpdir, ignore_errors=True)
            
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
            
    def _convert_with_dirs(self, tmpdir: str, outdir: str) -> None:
        """Helper method to perform conversion with given directories."""
        fp16 = str(Path(outdir)/f"{self.model_name}.fp16.gguf")
        
        # Download model
        local_dir = Path(tmpdir)/self.model_name
        console.print("[bold green]Downloading model...")
        api = HfApi(token=self.token)
        api.snapshot_download(
            repo_id=self.model_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        
        # Convert to fp16
        console.print("[bold green]Converting to fp16...")
        result = subprocess.run([
            "python", "llama.cpp/convert_hf_to_gguf.py",
            str(local_dir),
            "--outtype", "f16",
            "--outfile", fp16
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise ConversionError(f"Error converting to fp16: {result.stderr}")
            
        # If fp16_only is True, we're done after fp16 conversion
        if self.fp16_only:
            quantized_files = [f"{self.model_name}.fp16.gguf"]
            if self.username and self.token:
                api.upload_file(
                    path_or_fileobj=fp16,
                    path_in_repo=f"{self.model_name}.fp16.gguf",
                    repo_id=f"{self.username}/{self.model_name}-GGUF"
                )
            return
            
        # Generate importance matrix if needed
        imatrix_path: Optional[str] = None
        if self.use_imatrix:
            train_data_path = self.train_data_file if self.train_data_file else "llama.cpp/groups_merged.txt"
            imatrix_path = str(Path(outdir)/"imatrix.dat")
            self.generate_importance_matrix(fp16, train_data_path, imatrix_path)
        
        # Quantize model
        console.print("[bold green]Quantizing model...")
        quantized_files: List[str] = []
        for method in self.quantization_methods:
            quantized_name = f"{self.model_name.lower()}-{method.lower()}"
            if self.use_imatrix:
                quantized_name += "-imat"
            quantized_path = str(Path(outdir)/f"{quantized_name}.gguf")
            
            if self.use_imatrix:
                quantize_cmd: List[str] = [
                    "./llama.cpp/build/bin/llama-quantize",
                    "--imatrix", imatrix_path,
                    fp16, quantized_path, method
                ]
            else:
                quantize_cmd = [
                    "./llama.cpp/build/bin/llama-quantize",
                    fp16, quantized_path, method
                ]
            
            result = subprocess.run(quantize_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ConversionError(f"Error quantizing with {method}: {result.stderr}")
            
            quantized_files.append(f"{quantized_name}.gguf")
        
        # Split model if requested
        if self.split_model:
            split_files = self.split_model(quantized_path, outdir)
            if self.username and self.token:
                self.upload_split_files(split_files, outdir, f"{self.username}/{self.model_name}-GGUF")
        else:
            # Upload single file if credentials provided
            if self.username and self.token:
                api.upload_file(
                    path_or_fileobj=quantized_path,
                    path_in_repo=f"{self.model_name.lower()}-{self.quantization_methods[0].lower()}.gguf",
                    repo_id=f"{self.username}/{self.model_name}-GGUF"
                )
        
        # Upload imatrix if generated and credentials provided
        if imatrix_path and self.username and self.token:
            api.upload_file(
                path_or_fileobj=imatrix_path,
                path_in_repo="imatrix.dat",
                repo_id=f"{self.username}/{self.model_name}-GGUF"
            )
        
        # Generate and upload README if credentials provided
        if self.username and self.token:
            readme_content = self.generate_readme(quantized_files)
            self.upload_readme(readme_content, f"{self.username}/{self.model_name}-GGUF")

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
@option("-q", "--quantization", help="Comma-separated quantization methods", default="q4_k_m")
@option("-i", "--use-imatrix", help="Use importance matrix for quantization", is_flag=True)
@option("--train-data", help="Training data file for imatrix quantization", default=None)
@option("-s", "--split-model", help="Split the model into smaller chunks", is_flag=True)
@option("--split-max-tensors", help="Maximum number of tensors per file when splitting", default=256)
@option("--split-max-size", help="Maximum file size when splitting (e.g., '256M', '5G')", default=None)
def convert_command(
    model_id: str,
    username: Optional[str] = None,
    token: Optional[str] = None,
    quantization: str = "q4_k_m",
    use_imatrix: bool = False,
    train_data: Optional[str] = None,
    split_model: bool = False,
    split_max_tensors: int = 256,
    split_max_size: Optional[str] = None
) -> None:
    """
    Convert and quantize HuggingFace models to GGUF format! 🚀
    
    Args:
        model_id (str): Your model's HF ID (like 'OEvortex/HelpingAI-Lite-1.5T') 🎯
        username (str, optional): Your HF username for uploads 👤
        token (str, optional): Your HF API token 🔑
        quantization (str): Quantization methods (default: q4_k_m,q5_k_m) 🎮
        use_imatrix (bool): Use importance matrix for quantization 🔍
        train_data (str, optional): Training data file for imatrix quantization 📚
        split_model (bool): Split the model into smaller chunks 🔪
        split_max_tensors (int): Max tensors per file when splitting (default: 256) 📊
        split_max_size (str, optional): Max file size when splitting (e.g., '256M', '5G') 📏
        
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
            quantization_methods=quantization,
            use_imatrix=use_imatrix,
            train_data_file=train_data,
            split_model=split_model,
            split_max_tensors=split_max_tensors,
            split_max_size=split_max_size
        )
        converter.convert()
    except (ConversionError, ValueError) as e:
        console.print(f"[red]Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}")
        sys.exit(1)

def main() -> None:
    """Fire up the GGUF converter! 🚀"""
    app.run()

if __name__ == "__main__":
    main()
