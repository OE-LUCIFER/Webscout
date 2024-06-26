# webscout/Extra/gguf.py
import subprocess
import argparse
import os 

def convert(model_id, username=None, token=None, quantization_methods="q4_k_m,q5_k_m"):
    """Converts and quantizes a Hugging Face model to GGUF format.

    Args:
        model_id (str): The Hugging Face model ID (e.g., 'google/flan-t5-xl').
        username (str, optional): Your Hugging Face username. Required for uploads.
        token (str, optional): Your Hugging Face API token. Required for uploads. 
        quantization_methods (str, optional): Comma-separated quantization methods. 
                                                Defaults to "q4_k_m,q5_k_m".

    Raises:
        ValueError: If an invalid quantization method is provided.
    """

    # List of valid quantization methods
    valid_methods = [
        "q2_k", "q3_k_l", "q3_k_m", "q3_k_s", 
        "q4_0", "q4_1", "q4_k_m", "q4_k_s", 
        "q5_0", "q5_1", "q5_k_m", "q5_k_s", 
        "q6_k", "q8_0"
    ]
    
    # Validate the selected quantization methods
    selected_methods_list = quantization_methods.split(',')
    for method in selected_methods_list:
        if method not in valid_methods:
            raise ValueError(f"Invalid method: {method}. Please select from the available methods: {', '.join(valid_methods)}")
    
   # Construct the absolute path to the shell script
    script_path = os.path.join("webscout", "Extra", "gguf.sh")

    print(f"Script Path: {script_path}") # Print the path for debugging

    # Construct the command
    command = ["bash", script_path, "-m", model_id]
    
    if username:
        command.extend(["-u", username])
    
    if token:
        command.extend(["-t", token])
    
    if quantization_methods:
        command.extend(["-q", quantization_methods])
    
    # Execute the command
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Print the output and error in real-time
    for line in process.stdout:
        print(line, end='')

    for line in process.stderr:
        print(line, end='')
    
    process.wait()

def main():
    parser = argparse.ArgumentParser(description='Convert and quantize model using gguf.sh')
    parser.add_argument('-m', '--model_id', required=True, help='Set the HF model ID (e.g., "google/flan-t5-xl")')
    parser.add_argument('-u', '--username', help='Set your Hugging Face username (required for uploads)')
    parser.add_argument('-t', '--token', help='Set your Hugging Face API token (required for uploads)')
    parser.add_argument('-q', '--quantization_methods', default="q4_k_m,q5_k_m", 
                        help='Comma-separated quantization methods (default: q4_k_m,q5_k_m). Valid methods: q2_k, q3_k_l, q3_k_m, q3_k_s, q4_0, q4_1, q4_k_m, q4_k_s, q5_0, q5_1, q5_k_m, q5_k_s, q6_k, q8_0')
    
    args = parser.parse_args()
    
    try:
        convert(args.model_id, args.username, args.token, args.quantization_methods)
    except ValueError as e:
        print(e)
        exit(1)

if __name__ == "__main__":
    main()